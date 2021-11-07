import fitz
from fitz.fitz import Link, Pixmap
import math
from PIL import Image, ImageDraw
import sys

'''
将PDF转化为图片
pdfPath pdf文件的路径
imgPath 图像要保存的文件夹
zoom_x x方向的缩放系数
zoom_y y方向的缩放系数
rotation_angle 旋转角度
'''
def pdf_image(pdfPath, imgPath, zoom_x=5, zoom_y=5, rotation_angle=0):
    pdf_png_pages = list()
    # 打开PDF文件
    pdf = fitz.open(pdfPath)
    # 逐页读取PDF
    for pg in range(0, pdf.pageCount):
        print(f'第{pg+1}页转图像，共{pdf.pageCount}页...')
        page = pdf[pg]
        # 设置缩放和旋转系数
        trans = fitz.Matrix(zoom_x, zoom_y).prerotate(rotation_angle)
        pm = page.get_pixmap(matrix=trans, alpha=False)
        # 开始写图像
        pdf_png_pages.append(pm.tobytes(output='png'))
    pdf.close()
    return pdf_png_pages

'''
将多个图像合并到一页
images bytes类型的图像列表
page_number 一页上放几个图像
'''
def images_merge(images, images_number_in_one=5, blank_edge_pixels=60, LINE_PIXEL=3):
    import io
    pages_number = math.ceil(len(images) / images_number_in_one) # 合并后的总页数
    pages_images = list() # 所有合并后的页面
    single_image_size = Image.open(io.BytesIO(images[0])).size # 临时打开第一个图像获取尺寸
    for page_index in range(pages_number):
        print(f'第{page_index+1}页合并图像，共{pages_number}页...')
        # 新建空画布
        pages_images.append(Image.new('RGB', (
            single_image_size[0] * images_number_in_one + blank_edge_pixels*(images_number_in_one + 1), 
            single_image_size[1] + blank_edge_pixels*2), color='White')
        )
        for little_page_index in range(images_number_in_one):
            # 检测最后一页，如果超范围就跳出
            if page_index * images_number_in_one + little_page_index >= len(images):
                break

            # 打开图像
            im = Image.open(io.BytesIO(images[page_index * images_number_in_one + little_page_index]))
            # 在图像四周绘制边框
            ImageDraw.Draw(im).line(
                [
                    (0+LINE_PIXEL, 0+LINE_PIXEL), (single_image_size[0]-LINE_PIXEL, 0+LINE_PIXEL),
                    (0+LINE_PIXEL, 0+LINE_PIXEL), (0+LINE_PIXEL, single_image_size[1]-LINE_PIXEL),
                    (0+LINE_PIXEL, single_image_size[1]-LINE_PIXEL), (single_image_size[0]-LINE_PIXEL, single_image_size[1]-LINE_PIXEL),
                    (single_image_size[0]-LINE_PIXEL, single_image_size[1]-LINE_PIXEL), (single_image_size[0]-LINE_PIXEL, 0+LINE_PIXEL)
                ],
                fill='Black', width=LINE_PIXEL
                )
            # 图像放到空画布中
            pages_images[page_index].paste(im, (
                blank_edge_pixels*(little_page_index+1) + single_image_size[0]*little_page_index, 
                blank_edge_pixels, 
                blank_edge_pixels*(little_page_index+1) + single_image_size[0]*(little_page_index+1), 
                blank_edge_pixels+single_image_size[1]
                ))
        #pages_images[page_index].show()
    return pages_images

import PySimpleGUI as sg
import sys
import threading

# My function that takes a long time to do...
def my_long_operation(path, window):
    one_page_images_number = 5
    blank_edge_pixels = 60
    line_pixel = 3
    pdf_png_pages = pdf_image(path, path)
    pages = images_merge(pdf_png_pages, one_page_images_number, blank_edge_pixels, line_pixel)
    print('写出文件：')
    for page_index in range(len(pages)):
        print(f'{path}{page_index*one_page_images_number+1}-{((page_index+1)*one_page_images_number)}.png')
        im = pages[page_index].convert('RGB')
        im.save(f'{path}{page_index*one_page_images_number+1}-{((page_index+1)*one_page_images_number)}.png')
    print('成功：')

def main():
    if len(sys.argv) == 1:
        fname = sg.popup_get_file('选择要转换的pdf文件',file_types=(('PDF files', '*.pdf'),))
    else:
        fname = sys.argv[1]
 
    if not fname:
        sg.popup("Cancel", "No filename supplied")
        raise SystemExit("Cancelling: no filename supplied")
    else:
        path = fname

        layout = [  
            [sg.Multiline(size=(65,20), key='-ML-', autoscroll=True, reroute_stdout=True, write_only=True, reroute_cprint=True)],
            [sg.Button('Exit')]]

        window = sg.Window('Started', layout, keep_on_top=True, finalize=True)
        threading.Thread(target=my_long_operation, args=(path, window,), daemon=True).start()   

        while True:   
          # Event Loop
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == 'Exit':
                break
        window.close()

if __name__ == '__main__':
    main()

