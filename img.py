from io import BytesIO
import numpy as np
from PIL import Image, ImageFont, ImageDraw

    
class Img:


    _LINE_WIDTH = 1.5
    _DOTTED_LENGTH = 7.95
    _DOTTED_RATIO = 0.6
    _FONT = "arial.ttf"
    _FONT_SIZE = 10
    _SPACING = 2
    _STROKE_FILL = "white"
    _STROKE_WIDTH = 1


    def __init__(self, lims: tuple[float, float, float, float], paper_size: tuple[float, float], dpi: float) -> None:
        self.xmin, self.xmax, self.ymin, self.ymax = lims
        self.dpi = dpi
        paper_width, paper_height = paper_size
        self.width: int = self.paper2img_len(paper_width)
        self.height: int = self.paper2img_len(paper_height)
        self.img = Image.new("RGB", (self.width, self.height))
        self.font = ImageFont.truetype(self._FONT, size=self.font2img_len(self._FONT_SIZE), encoding="unic")


    def lines(self, x: list[float], y: list[float], color: str, line_width: float=None) -> None:
        if line_width == None: line_width = self._LINE_WIDTH
        x = np.array(x)
        y = np.array(y)
        i = self.data2img_i(x, self.xmin, self.xmax, self.width)
        j = self.data2img_j(y, self.ymin, self.ymax, self.height)
        ij = np.array([i, j]).flatten("F").tolist()
        draw = ImageDraw.Draw(self.img)
        draw.line(ij, fill=color, width=self.font2img_len(line_width), joint="curve")

    def dotted(self, x: list[float], y: list[float], color: str, line_width: float=None, dotted_length: float=None, dotted_ratio: float=None) -> None:
        if line_width == None: line_width = self._LINE_WIDTH
        if dotted_length == None: dotted_length = self._DOTTED_LENGTH
        if dotted_ratio == None: dotted_ratio = self._DOTTED_RATIO

        x = np.array(x)
        y = np.array(y)
        slices = np.ma.clump_masked(np.ma.masked_where(np.logical_and(np.logical_and(x<self.xmax, x>self.xmin), np.logical_and(y<self.ymax, y>self.ymin)), x))
        for slice in slices:
            start = slice.start
            stop = slice.stop
            if start > 0: start -= 1
            if stop < x.size-1: stop += 1

            slice_i = self.data2img_i(x[start:stop], self.xmin, self.xmax, self.width)
            slice_j = self.data2img_j(y[start:stop], self.ymin, self.ymax, self.height)
            slice_length = np.sqrt(np.sum(np.power((slice_i - slice_j), 2)))
            func = lambda a:  np.sqrt(np.power(a[0]-a[2], 2) + np.power(a[1]-a[3], 2))
            delta = np.insert(np.apply_along_axis(func, 1, np.column_stack((slice_i[:-1], slice_j[:-1], slice_i[1:], slice_j[1:]))), 0, 0)
            slice_length = np.cumsum(delta)

            prev_idx = 0
            while True:

                i = slice_i[prev_idx:]
                j = slice_j[prev_idx:]
                length = slice_length[prev_idx:]
                if prev_idx > 0: 
                    i = np.insert(i, 0, i_interp)
                    j = np.insert(j, 0, j_interp)
                    length = np.insert(length, 0, length_interp)
                
                draw_length = length[0] + dotted_ratio*self.font2img_len(dotted_length)
                idx = np.argmax(length > draw_length)
                if idx == 0: break
                i1 = i[idx-1]
                j1 = j[idx-1]
                length1 = length[idx-1]
                i2 = i[idx]
                j2 = j[idx]
                length2 = length[idx]
                t = (length2 - draw_length)/(length2 - length1)
                i_interp = i2 - t*(i2 - i1)
                j_interp = j2 - t*(j2 - j1)
                # Drawing
                ij = np.array([np.append(i[:idx], i_interp), np.append(j[:idx], j_interp)]).flatten("F").tolist()
                draw = ImageDraw.Draw(self.img)
                draw.line(ij, fill=color, width=self.font2img_len(line_width), joint="curve")

                total_length = length[0] + self.font2img_len(dotted_length)
                idx = np.argmax(length > total_length)
                if idx == 0: break
                i1 = i[idx-1]
                j1 = j[idx-1]
                length1 = length[idx-1]
                i2 = i[idx]
                j2 = j[idx]
                length2 = length[idx]
                t = (length2 - total_length)/(length2 - length1)
                i_interp = i2 - t*(i2 - i1)
                j_interp = j2 - t*(j2 - j1)
                length_interp = total_length

                if prev_idx == 0: prev_idx = idx
                else: prev_idx += idx-1

            ij = np.array([i, j]).flatten("F").tolist()
            draw = ImageDraw.Draw(self.img)
            draw.line(ij, fill=color, width=self.font2img_len(line_width), joint="curve")


    def text(self, x: float, y: float, text: str, color: str, angle: float=0) -> None:

        bbox = self.font.getbbox(text, stroke_width=self.font2img_len(self._STROKE_WIDTH))
        text_width, text_height = bbox[2], bbox[3]
        box = Image.new("RGB", (text_width, text_height))
        mask = Image.new("L", (text_width, text_height))
    
        box_draw = ImageDraw.Draw(box)
        mask_draw = ImageDraw.Draw(mask)
        box_draw.text([0, 0], text, fill=color, font=self.font, stroke_width=self.font2img_len(self._STROKE_WIDTH), stroke_fill=self._STROKE_FILL)
        mask_draw.text([0, 0], text, fill="white", font=self.font, stroke_fill="white", stroke_width=self.font2img_len(self._STROKE_WIDTH))

        box = box.rotate(angle, Image.Resampling.BICUBIC, expand=True)
        mask = mask.rotate(angle, Image.Resampling.BICUBIC, expand=True)

        i = self.data2img_i(x, self.xmin, self.xmax, self.width)
        j = self.data2img_j(y, self.ymin, self.ymax, self.height)
        if angle % 360 <= 90:
            i -=  text_height*np.cos(np.deg2rad(90 - angle))
            j -=  box.height
        elif (angle-90) % 360 <= 90:
            i -=  box.width
            j -=  text_width*np.cos(np.deg2rad(angle - 90))
            box = box.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
            mask = mask.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
        elif (angle-180) % 360 <= 90:
            i -=  text_width*np.cos(np.deg2rad(angle - 180))
            box = box.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
            mask = mask.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
        else:
            j -=  text_height*np.cos(np.deg2rad(angle - 260))
        ij = [int(i), int(j)]
        self.img.paste(box, ij, mask)

    def annotate(self, x: float, y: float, text: str, color: str, angle: float=0, distance: float=None) -> None:
        if distance == None: distance = self.font2img_len(self._FONT_SIZE)/2
        i0 = self.data2img_i(x, self.xmin, self.xmax, self.width)
        j0 = self.data2img_j(y, self.ymin, self.ymax, self.height)
        i = i0 + distance*np.cos(np.deg2rad(angle))
        j = j0 - distance*np.sin(np.deg2rad(angle))
        ij = [i, j]
        draw = ImageDraw.Draw(self.img)
        anchors = ["lm", "ls", "ms", "rs", "rm", "rt", "mt", "lt"]
        for i, anchor in enumerate(anchors): 
            # See https://stackoverflow.com/a/66834497
            if (angle - (i-1/2)*45) % 360 <= 45: 
                break
        kwargs = {"font": self.font, "anchor": anchor, "spacing": self.font2img_len(self._SPACING), "stroke_width": self.font2img_len(self._STROKE_WIDTH), "stroke_fill": self._STROKE_FILL}
        draw.text(ij, text, color, **kwargs)


    def mark(self, x: float, y: float, color: str, angle: float=0, length: float=None, line_width: float=None) -> None:
        if length == None: length = self.font2img_len(self._FONT_SIZE)
        if line_width == None: line_width = self._LINE_WIDTH
        i0 = self.data2img_i(x, self.xmin, self.xmax, self.width)
        j0 = self.data2img_j(y, self.ymin, self.ymax, self.height)
        i1 = i0 - length/2*np.cos(np.deg2rad(angle))
        j1 = j0 + length/2*np.sin(np.deg2rad(angle))
        i2 = i0 + length/2*np.cos(np.deg2rad(angle))
        j2 = j0 - length/2*np.sin(np.deg2rad(angle))
        ij = [i1, j1, i2, j2]
        draw = ImageDraw.Draw(self.img)
        draw.line(ij, fill=color, width=self.font2img_len(line_width), joint="curve")

    
    def paste(self, img_str: str, lims: tuple[float, float, float, float]):
        img = Image.open(BytesIO(img_str.content))
        imin = self.data2img_i(lims[0])
        imax = self.data2img_i(lims[1])
        jmin = self.data2img_j(lims[2])
        jmax = self.data2img_j(lims[3])
        img = map.resize(self.img.size, resample=Image.Resampling.LANCZOS, box=(imin, jmin, imax, jmax))
        self.img.paste(img)


    def scalebar(self, scale_len: float, scale_dist: float, unit: str) -> None:
        bar_width = self.paper2img_len(scale_len)
        bar_height = self.font2img_len(self._FONT_SIZE)
        draw = ImageDraw.Draw(self.img)
        draw.rectangle([0, self.height-bar_height, bar_width/4, self.height], fill="black")
        draw.rectangle([bar_width/4, self.height-bar_height, bar_width/2, self.height], fill="white", outline="black", width=self.font2img_len(self._LINE_WIDTH))
        draw.rectangle([bar_width/2, self.height-bar_height, 3*bar_width/4, self.height], fill="black")
        draw.rectangle([3*bar_width/4, self.height-bar_height, bar_width, self.height], fill="white", outline="black", width=self.font2img_len(self._LINE_WIDTH))
        kwargs = {"fill": "black", "font": self.font, "spacing": self.font2img_len(self._SPACING), "stroke_width": self.font2img_len(self._STROKE_WIDTH), "stroke_fill": self._STROKE_FILL}
        draw.text([0, self.height-bar_height], "0", anchor="ls", **kwargs) 
        draw.text([bar_width/2, self.height-bar_height], f"{np.round(scale_dist/2,2):g}", anchor="ms", **kwargs)
        draw.text([bar_width, self.height-bar_height], f"{np.round(scale_dist,2):g}", anchor="rs", **kwargs)
        draw.text([bar_width, self.height-bar_height], unit, anchor="ls", **kwargs)


    def show(self) -> None:
        self.img.show()

    def save(self, name: str, append_images=None) -> None:
        self.img.save(name, save_all=append_images is not None, append_images=[img.img for img in append_images])


    # Image projection
    @staticmethod
    def data2img_i(x, xmin, xmax, width):
        i = (x-xmin)/(xmax-xmin)*width
        return i
    @staticmethod
    def data2img_j(y, ymin, ymax, height):
        j = (ymax-y)/(ymax-ymin)*height
        return j
    
    # Converting lengths
    @staticmethod
    def font2paper_len(font_len):
        paper_len = 0.0353*font_len
        return paper_len
    def paper2img_len(self, paper_len):
        img_len = int(self.dpi/2.54*paper_len)
        return img_len
    def font2img_len(self, font_len):
        img_len = self.paper2img_len(Img.font2paper_len(font_len))
        return img_len


if __name__ == "__main__":
    img = Img((0, 3, -5, 5), (10, 10), 500)
    r = 0.3
    x = np.linspace(0, 10, 1000)
    y = lambda x: np.sin(r**2 - x**2)
    yprime = lambda x: -2*x*np.cos(r**2 - x**2)
    img.lines(x, y(x), "red")
    for x in np.linspace(0, 10, 20):
        m = yprime(x)
        angle = np.rad2deg(np.arctan(m)) - 90
        img.mark(x, y(x), "red", angle)
        img.annotate(x, y(x), str(int(angle)), "black", angle)
        angle = angle + 90
        img.text(x, y(x), f"der winkel beträgt {int(angle)}°", "purple", angle)
    img.show()



