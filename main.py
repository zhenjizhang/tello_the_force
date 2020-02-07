#main函数，主循环代码放这里
import cv2
import pygame
import time
import numpy

import time 
from Tello import Tello
from simple_pid import PID
from UI import FPS,UID
from math import atan2, degrees, sqrt,pi,atan
from Pose import Pose
from Com import*
#import profile

#未完成整理待续

global ispose
global us
global isposetime
isposetime=time.time()
ispose=0
us=[0,0,0,0,0,0]
def usec(key_list):#定义键盘跟踪，暂时没有封转到类
    speed=50
    global us
    global ispose
    global isposetime
    for i in [0,1,2,3,5]:
        us[i]=0
    
    #除了第4都归零，感觉是多余的
    if key_list[pygame.K_w]:#W 前进
        us[1]=speed
    if key_list[pygame.K_s]:#s后退
        us[1]=-speed
    if key_list[pygame.K_q]:#q
        us[2]=-speed
    if key_list[pygame.K_e]:#e
        us[2]=speed
    if key_list[pygame.K_a]:#a
        us[3]=-speed
    if key_list[pygame.K_d]:#d
        us[3]=speed
    if key_list[pygame.K_LSHIFT]:#shitf
        us[0]=speed
    if key_list[pygame.K_LCTRL]:#ctrl
        us[0]=-speed
    #ispose
    if key_list[pygame.K_t]:
        if ispose !=1:
            if time.time()-isposetime>2:
                us[4]=1
                isposetime=time.time() 
                ispose=1
                #screen = pygame.display.set_mode((640, 480), 0)
        else:
            if  time.time()-isposetime>2:
                us[4]=0
                isposetime=time.time()
                ispose=0
                #screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN | pygame.HWSURFACE)
    #全屏切换
    if key_list[pygame.K_F11]:
        screen = pygame.display.set_mode((640, 480), 0)
    if key_list[pygame.K_F12]:
        screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN | pygame.HWSURFACE)
    #特殊指令执行时通道指令无效且归零
    if key_list[pygame.K_0]:#0
        us[5]=2
        us[0]=us[1]=us[2]=us[3]=0
        
    if key_list[pygame.K_9]:#退出
        us[5]=3
        us[0]=us[1]=us[2]=us[3]=0
        
    
    elif key_list[pygame.K_UP]:#up
        #四通道值刷为0
        us[5]=1
        us[0]=us[1]=us[2]=us[3]=0
        
    elif key_list[pygame.K_DOWN]: #down
        #四通道值刷为0
        us[5]=4
        us[0]=us[1]=us[2]=us[3]=0

    elif key_list[pygame.K_SPACE]:#space紧急停机
        pass
        #四个通道刷为0
         #[0  1  2  3   4         5]
           #四个通道   ispose    模式
        #油 pitch roll yaw ispose   模式 0   1   2     3         4             
      #shift w     e    a    t          无  起飞 抛飞  降落  手掌降落  
       #ctrl  s    q    d    t              up down   0         0   
    
    #八向翻滚：5  6 7 8  9 10  11 12 
    #对应键位  8  2 4 6  7  9  1  3
    elif key_list[pygame.K_KP8]:
        us[5]=5
        us[0]=us[1]=us[2]=us[3]=0
    elif key_list[pygame.K_KP2]:
        us[5]=6
        us[0]=us[1]=us[2]=us[3]=0
    elif key_list[pygame.K_KP4]:
        us[5]=7
        us[0]=us[1]=us[2]=us[3]=0
    elif key_list[pygame.K_KP6]:
        us[5]=8
        us[0]=us[1]=us[2]=us[3]=0
    elif key_list[pygame.K_KP7]:
        us[5]=9
        us[0]=us[1]=us[2]=us[3]=0
    elif key_list[pygame.K_KP9]:
        us[5]=10
        us[0]=us[1]=us[2]=us[3]=0
    elif key_list[pygame.K_KP1]:
        us[5]=11
        us[0]=us[1]=us[2]=us[3]=0
    elif key_list[pygame.K_KP3]:
        us[5]=12
        us[0]=us[1]=us[2]=us[3]=0
    return us

def pygdisplaycv2(imsurface):
    #cv2.resize(imsurface,(w,h))
    imsurface=cv2.cvtColor(imsurface, cv2.COLOR_BGR2RGB)
    imsurface=numpy.rot90(imsurface,k=-1)
    imsf=pygame.surfarray.make_surface(imsurface)
    imsf = pygame.transform.flip(imsf, False, True)
    return imsf



def main():
    isdisplay=1
    
    tello=Tello()

    pygame.init()
    pygame.mixer.init()

    if isdisplay==1:
        screen = pygame.display.set_mode((640, 480), 0)#键盘控制封不了类，只能用函数
        pygame.display.set_caption('没卵用的窗口')
        #不会动的界面
        background=pygame.image.load('media//uimain.png')
        #俯仰滚
        roll=pygame.image.load('media//roll.png')
        rollrect=roll.get_rect()
        #电池速度高度
        heightp=pygame.image.load('media//h.png')
        betp=pygame.image.load('media//battery.png')
        velhp=pygame.image.load('media//velh.png')
        velxyp=pygame.image.load('media//velxy.png')
        #转盘
        yawp=pygame.image.load('media//yawpoint.png')
        yawprect=yawp.get_rect()
        #飞行模式和灯
        ready=pygame.image.load('media//ready.png')
        pl=pygame.image.load('media//pl.png')
        flying=pygame.image.load('media//visualfly.png')
        greenlight=pygame.image.load('media//greenlight.png')
        redlight=pygame.image.load('media//redlight.png')

    else:
        screen = pygame.display.set_mode((320, 240), 0, 32)#键盘控制封不了类，只能用函数
        pygame.display.set_caption('没卵用的窗口')
        background=pygame.image.load('media//tello background1.png')

    ui=UID()
    pose=Pose()
    com=Com()

    frame_skip=300
    try:
        for frame in tello.container.decode(video=0):#一定要用这个循环来获取才不会产生delay
            if 0 < frame_skip:
                frame_skip = frame_skip - 1
                continue
            start_time = time.time()
            image = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
            key_list = pygame.key.get_pressed()
            imageraw=image
            image = cv2.resize(image,(640,480))#这个太大会爆显存

            userc=usec(key_list)#来自用户输入的命令
            #userc[0                1 2 3 4   5         ]
                #是否使用openpose    四个通道  模式
            if userc[4]==1:#判断使用跟踪
                kp=pose.get_kp(image)
            else:#不使用
                kp=[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]]
            comd=com.get_comd(kp,userc)#接受两个数组进行判断
            tello.send_comd(comd)
            flight=tello.send_data()#飞行数据
            com.read_tello_data(flight)#飞控获取数据用于判断指令
            flightstate=com.get_state()#命令状态
            
            if isdisplay==1:
                #背景和画面
                imsf=pygdisplaycv2(image)
                screen.blit(imsf,(0,0))
                screen.blit(background,(0,0))
                #滚动俯
                newroll=pygame.transform.rotate(roll,-(180/pi)*atan(flightstate[15]/5))#使用响应曲线放大
                newrect=newroll.get_rect(center=rollrect.center)
                screen.blit(newroll,(newrect[0]+264,newrect[1]+129-(366/pi)*atan(flightstate[16]/5)))#使用响应曲线放大
                #电池高度速度
                screen.blit(heightp,(5,319-abs(flightstate[11]*12)))
                screen.blit(betp,(575-(100-flightstate[1])*4,18))
                screen.blit(velhp,(611,283+int(flightstate[18]*4)))
                screen.blit(velxyp,(611,211-int(flightstate[17]*10)))
                #盘
                newyawp=pygame.transform.rotate(yawp,-flightstate[24])
                newyawprect=newyawp.get_rect(center=yawprect.center)
                screen.blit(newyawp,(newyawprect[0]+74,newyawprect[1]+368))#使用响应曲线放大
                #飞行模式和灯
                if flightstate[0]!=0:#飞行中
                    if flightstate[25]==6:
                        screen.blit(flying,(13,10))
                    elif flightstate[25]==1:
                        screen.blit(pl,(23,11))
                    #灯
                    screen.blit(greenlight,(601,6))
                else:
                    if flightstate[25]==6:
                        screen.blit(ready,(17,8))
                    elif flightstate[25]==1:
                        screen.blit(pl,(23,11))
                    screen.blit(redlight,(601,6))

                pygame.display.update()
            else:
                screen.blit(background,(0,0))
                pygame.display.update()

            

            if userc[4]==1:#使用
                ui.show(image,kp,flightstate)#显示并负责播放声音
            else:#不用
                ui.show(imageraw,0,flightstate)
            
            if frame.time_base < 1.0/60:
                time_base = 1.0/60
            else:
                time_base = frame.time_base
            frame_skip = int((time.time() - start_time)/time_base)
            k = cv2.waitKey(1) & 0xff
            if k == 27 : 
                pygame.display.quit()
                tello.drone.quit()#退出
                break
        
    except:
        print('连接超时或发生错误退出辽')

    cv2.destroyAllWindows()#关掉飞机直接退出程序
    tello.drone.quit()
    pygame.display.quit()
    

if __name__=='__main__':
    main()
    #rofile.run("main()")

        