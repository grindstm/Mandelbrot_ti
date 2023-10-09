# controls for zoom, exponent, and max_iters. Pan


# make a 3d one with spheres

import taichi as ti
import taichi.math as tm
from time import perf_counter

ti.init(arch=ti.gpu, default_ip=ti.i32, default_fp=ti.f32)

vec3 = ti.types.vector(3, float)
vec2 = ti.types.vector(2, float)
mat2=ti.types.matrix(2, 2, float)
mat3=ti.types.matrix(3, 3, float)


class Pair:
    def __init__(self, im1, im2):                                                                                                                    
        self.cur = im1                                                                                  
        self.nxt = im2
                                                                                                                                          
    def swap(self):
        self.cur, self.nxt = self.nxt, self.cur

res=(768,768)

im = ti.Vector.field(3, float, shape=res)
im_ = ti.Vector.field(3, float, shape=res)
ims = Pair(im, im_)

mouse = ti.Vector.field(2, float, shape=1)
t = ti.field(float, shape=1)



@ti.kernel
def init():
    for i, j in im:
        ims.nxt[i,j]=vec3(0.6)
        ims.cur[i,j]=vec3(0.1)

# @ti.func
# def rgb2hsl(c: vec3):
#     K = ti.Vector([0., -1. / 3., 2. / 3., -1.])
#     p = tm.mix(ti.Vector([c.z, c.y, K.w]), ti.Vector([c.y, c.z, K.z]), tm.step(c.z, c.y))
#     q = tm.mix(ti.Vector([p.x, p.y, p.w]), ti.Vector([p.x, p.y, p.z]), tm.step(p.x, c.x))
#     d = q.x - tm.min(q.w, q.y)
#     e = 1e-10
#     return ti.Vector([tm.abs(q.z + (q.w - q.y) / (6. * d + e)), d / (q.x + e), q.x])

# ========================================================
zoom=ti.field(float,shape=1)
zoom_delta=ti.field(float,shape=1)
zoom_delta[0]=1.2
zoom[0]=0.
pan=ti.Vector.field(2, float, shape=1)
pan[0]=vec2(0.)
click = ti.Vector.field(2, float, shape =1)
clicked=ti.field(int, shape=1)
clicked[0]=0

@ti.func
def coord(i,j):
    return vec2(2*i/res[0]-1,1-(2*j/res[1]))

@ti.func
def pan_zoom(c):
    c+=pan[0]
    S=mat2((1/zoom[0],0),(0,1/zoom[0]))
    return S@(c-click[0])+click[0]

exponent = ti.field(float, shape=1)
exponent[0]=2.
max_iters = ti.field(int, shape=1)
max_iters[0]=100
limit = ti.field(float, shape=1)
limit[0] = 2.

highest_iters=0

@ti.func
def mandelbrot(i, j):
    Z=c=coord(i,j)
    # Z=c=coord(i,j)
    # Z=c=pan_zoom(coord(i,j))
    # print(c)
    out=0
    # if tm.length(Z)>limit[0]:
    #     out=0
    #     nxt[i,j]=vec3(0.5,0.65,0.5)

    # else:
    # print('in')
    # count=0
    for n in range(max_iters[0]):
        # count+=1
        Z=Z*tm.cpow(Z,exponent[0])+c   
        if tm.length(Z)>limit[0]:
            # r=n/max_iters[0]
            out=n
    # out=max_iters[0]

    return out
        # if count > highest_iters:
        #     highest_iters=count
        #     print(highest_iters)

# ========================================================

@ti.func
def paint_with_mouse(i,j,cur, lmb, size):
    distance=tm.distance(mouse[0], (i,j))
    return cur[i,j]+vec3(0.,0.,lmb*tm.smoothstep(.8,0.0,distance/size))

@ti.kernel 
def nxt_frame(nxt: ti.template(), cur:ti.template(), lmb: bool, rmb: bool):
    max_previous=0
    for i, j in im:
        l=tm.length(nxt[i,j])
        if l>max_previous:
            max_previous=l

    for i, j in im:
        nxt[i,j]=vec3(float(mandelbrot(i,j)/max_previous))
        
                # nxt[i,j] = vec3(0.5,0.5,0.5)

# def options(window):
#     gui=window.get_gui()
#     with gui.sub_window("_",x=0.,y=0.,width=1.,height=.2):
#         exponent[0]=gui.slider_float("exp: ", exponent[0],0.,10.)

        
def main():

    paused = False

    window=ti.ui.Window(name="Don't get a migraine", res=res, vsync=False)
    canvas = window.get_canvas()
    scene = ti.ui.Scene()
    camera = ti.ui.Camera()
    scene.set_camera(camera)
    canvas.scene(scene)
    # options(window)

    gui=window.get_gui()
    
    # init()

    while window.running:

        cursor_pos = window.get_cursor_pos()
        mouse[0].x = cursor_pos[0]
        mouse[0].y = cursor_pos[1]


        with gui.sub_window("_",x=0.,y=0.,width=1.,height=.15):
            max_iters[0]=gui.slider_int("max_iters ", max_iters[0],0,1000)
            limit[0]=gui.slider_float("limit",limit[0],0.,10.)
            exponent[0]=gui.slider_float("exp", exponent[0],0.,20.)
        start=vec2(0.)
        if window.get_event(ti.ui.PRESS):
            start=mouse[0].x
            print("press start", start)
        if window.get_event(ti.ui.RELEASE):
            print("start",start)
            print("mouse",mouse[0])
            if start!=mouse[0]:
                pan[0]=mouse[0]-start
                print("pan",pan)
            else:
                click[0] = mouse[0]
                clicked[0]=1
                print(click[0])
            e = window.event
            if e.key == ti.ui.ESCAPE:
                break
            elif e.key == 'p':
                paused = not paused
               

        t[0]=perf_counter()

        if not paused:
            nxt_frame(ims.nxt, ims.cur, window.is_pressed(ti.ui.LMB),window.is_pressed(ti.ui.RMB))
            ims.swap()
            canvas.set_image(ims.cur)

            window.show()
        if clicked[0]:
            print("clicked")
            zoom[0]+=zoom_delta[0]
            clicked[0]=0


if __name__=="__main__":
    main()