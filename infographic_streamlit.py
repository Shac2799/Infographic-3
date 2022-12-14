import streamlit as st
import numpy as np 
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import math
import pandas as pd
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import time
import plotly.express as px

st.set_page_config(page_title="Gravity Simulation", page_icon=None, 
                   layout="wide", initial_sidebar_state="auto", menu_items=None) 

st.title("Simulation of gravity between bodies")

class Body:
      G = 6.67428e-11 #gravitational constant
      solar_mass = 1.98892e30 # mass of sun in kg
      danger_bound = 0.3*149.6e9 # 1/5 of AU to sun as boundary 
      
      def __init__(self,radius,mass,x,y):
         
          self.radius = radius
          self.mass = mass*self.solar_mass # so user can change weight in solar mass
          self.x = x   # coords of centre of star/body
          self.y = y
          
      def density(self):
          volume = (4/3)*np.pi*self.radius**3
          return self.mass/volume     
        
      def gravity(self):          
          return (self.G*self.mass)/(self.radius**2)  # g = GM/r^2
      
        
class Object:
    AU = 149.6e9 # Astronomical units in metres
    time_interval = 86400 #3600  # number of seconds in a day
    No_danger = True # The object starts off outside of the body, if inside then this is false
    G = 6.67428e-11 
    
    def __init__(self,x,y,velocity,mass,num_days):
        
        self.x = x*self.AU # converting from AU to m
        self.y = y*self.AU
        self.mass = mass # mass in kg
        self.num_days = num_days # defining duration of graphic
        self.distance = 0
        self.path_x = [self.x/self.AU] # storing coordinates of object in number of AU
        self.path_y = [self.y/self.AU]
        self.x_vel = 0 #initialise x vel 
        self.y_vel = velocity*1000 # initial velocity in m/s
#         self.L = []
#         self.KE,self.PE = [], []
        
    def danger_zone(self,body):
          if abs(self.x) <=  body.danger_bound and abs(self.y) <= body.danger_bound:
              self.No_danger = False
          else:
              self.No_danger = True
              
        
    def force_of_attract(self,body):  # calculates gravitational force of attraction between bodies
        pos_x = body.x - self.x # coords of object relative to star/body
        pos_y = body.y - self.y             
        if pos_x == 0:
            theta = np.pi/2
        else:
            theta = math.atan2(pos_y,pos_x) # atan2 goes from -pi to pi (atan only pi/2)
        distance_metres = math.sqrt(pos_x**2 + pos_y**2) # distance between body and object
        force = (body.G*self.mass*body.mass)/(distance_metres**2) # total grav force
        fy = force*math.sin(theta)  # force in x and y directions
        fx = force*math.cos(theta)
        self.distance = distance_metres
#         self.L.append(self.mass*self.y_vel*distance_metres)
#         self.KE.append(0.5*self.mass*(self.y_vel**2)) # 1/2mv^2
#         self.PE.append(-force*distance_metres) # -GMm/r               

        return fx,fy
        
    def cowells(self,body,objects):
        net_fx, net_fy = self.force_of_attract(body)
        
        for obj in objects:
          if self == obj:
            continue
          fx,fy = self.force_of_attract(obj)
          net_fx += fx
          net_fy += fy
        return net_fx, net_fy
      
    def update_path(self,body,objects): # F = ma -> a = (v-u)/t -> v = Ft/m + u
  
        #using fourth order yoshida leapfrog integrator
        w0, w1 = -(np.cbrt(2)/(2-np.cbrt(2))), (1/(2-np.cbrt(2)))
        d1 =  d3 = w1
        d2 = w0
        c1 = c4 = w1/2
        c2 = c3 = (w0+w1)/2
        
        #intemediary steps between each time interval for x velocity
        #coefficients sum to 1 to ensure that total dt = time_interval
        self.x += c1*self.x_vel*self.time_interval #x1
        self.x_vel += d1*(self.cowells(body,objects)[0]/self.mass)*self.time_interval #v1
        self.x += c2*self.x_vel*self.time_interval # x2
        self.x_vel += d2*(self.cowells(body,objects)[0]/self.mass)*self.time_interval #v2
        self.x += c3*self.x_vel*self.time_interval # x3      
        self.x_vel += d3*(self.cowells(body,objects)[0]/self.mass)*self.time_interval #v3
        self.x += c4*self.x_vel*self.time_interval # x4
        
        self.path_x.append(self.x/self.AU) # storing position in array
#         self.xvel_list[self.i] = self.x_vel
        
        self.y += c1*self.y_vel*self.time_interval #x1
        self.y_vel += d1*(self.cowells(body,objects)[1]/self.mass)*self.time_interval #v1
        self.y += c2*self.y_vel*self.time_interval # x2
        self.y_vel += d2*(self.cowells(body,objects)[1]/self.mass)*self.time_interval #v2
        self.y += c3*self.y_vel*self.time_interval # x3      
        self.y_vel += d3*(self.cowells(body,objects)[1]/self.mass)*self.time_interval #v3
        self.y += c4*self.y_vel*self.time_interval # x4
        
        self.path_y.append(self.y/self.AU)

    def rescale_grid(self,image,x_limit,y_limit):    # 480 x 853 for stars.jpg
        height,width,_ = image.shape # dimensions of image
        image_xlim = image_ylim = [0,height]
        #image_xlim, image_ylim = [0,width], [0,height] # setting limits for grid as image dimensions
        new_centrex = new_centrey = height/2 # coords for centre of image
#         x_scale = width/sum(abs(np.array(x_limit))) # number of pixels within the limits
        x_scale = height/sum(abs(np.array(x_limit)))
        y_scale = height/sum(abs(np.array(y_limit)))
        img_posx = [(posx*x_scale + new_centrex) for posx in self.path_x] # calculating the re-scaled positions relative to image 
        img_posy = [(posy*y_scale + new_centrey) for posy in self.path_y]
        return img_posx, img_posy, image_xlim, image_ylim
      
    
def main():
    # choose steps/values for sliders
    # four inputs to select starting position of Earth/asteroid 
    with st.form(key='columns_in_form'):
        c1, c2, c3, c4 = st.columns(4)
    with c1:
        initx_earth = st.number_input("Earth x coord",step = 1.0, value = -1.0, min_value = -3.0,max_value = 3.0)
    with c2:
        inity_earth = st.number_input("Earth y coord", step = 1.0, value = 0.0, min_value = -3.0,max_value = 3.0)
    with c3:
        initx_ast = st.number_input("Asteroid x coord", step = 1.0, value = -2.0, min_value = -3.0,max_value = 3.0)
    with c4:
        inity_ast = st.number_input("Asteroid y coord", step = 1.0, value = 0.0, min_value = -3.0,max_value = 3.0)
        submitButton = st.form_submit_button(label = 'Set Coordinates')
        
    if initx_earth == 0 and inity_earth == 0:
        initx_earth = -1
        inity_earth = 0
        st.write('The Earth cannot be positioned on the Sun!')
    if initx_ast == 0 and inity_ast == 0:
        initx_ast = -2
        inity_ast = 0
        st.write('The asteroid cannot be positioned on the Sun!')
    if initx_earth == initx_ast and inity_earth == inity_ast:
        initx_earth, inity_earth = -1, 0
        initx_ast, inity_ast = -2, 0
        st.write('You cannot place both bodies in the same position!')
        
    mass_ast = st.number_input("Select the mass of the asteroid [Earth masses]", step = 5.0, value = 1.0, min_value = 1e-30)
    conv_mass = mass_ast*5.97e24
    st.write("The asteroid's mass is ",conv_mass, " kg")
    
    mass_body = st.slider("Mass of Sun [Solar mass]", min_value = 1.0, max_value = 10.0, step = 0.5, value = 1.0) 
    init_vel1 = st.slider("Asteroid initial orbital velocity [km/s]", min_value = -30.0, max_value = 30.0, step = 5.0, value = -15.0)
    init_vel2 = st.slider("Earth initial orbital velocity [km/s]", min_value = -30.0, max_value = 30.0, step = 5.0, value = -30.0)
    Days = st.slider("Duration [days]",min_value = 0.0, max_value = 5000.0, step = 5.0,value = 0.0)
    
        # if user wants to display asteroid they can select the option
    choice = st.radio("Select an option", ("Add asteroid","Remove asteroid"))
    #initiate instances of each object/body
    asteroid = Object(initx_ast,inity_ast,init_vel1,conv_mass,Days)
    Earth = Object(initx_earth,inity_earth,init_vel2,5.97e24,Days) 
    sun = Body(6.96e8,mass_body,0,0)
    
    #import all images for plot
    stars = mpimg.imread("stars2.jpg") 
    Sun_img = mpimg.imread("Sun.png")
    Earth_img = mpimg.imread("Earth2.png")
    Asteroid_img = mpimg.imread("meteor2.png")
    

    height,width,_ = stars.shape # dimensions of background image
    #re-scaling central body's position
    sun_scaledx = sun_scaledy = height/2 # setting sun's initial position at centre of image
    x_lim = y_lim = [-4,4] # -4 to 4 AU limits
          
    if choice == "Add asteroid":      
      objects = [Earth,asteroid]
    else:
      objects = [Earth]

    for day in range(int(Days)): # multiply by 24 if want timestep in hours
      for obj in objects:
          obj.danger_zone(sun)
          if obj.No_danger == True:
            obj.update_path(sun,objects)
          else:
            continue
    #re-scaling to image dimensions
    earth_x,earth_y,xlim,ylim = Earth.rescale_grid(stars, x_lim, y_lim) 
    asteroid_x,asteroid_y,_,_ = asteroid.rescale_grid(stars, x_lim, y_lim) 
    #defining parameters to change axes limits to AU
    AU = np.arange(x_lim[0],x_lim[1]+1,1)
    oldx = oldy = np.linspace(0,height,len(AU))
    
    #creating figure for plot
    fig,ax = plt.subplots()
    ax.set_aspect('equal')
    stars_cropped = stars[0:height,0:height,:] # cropping image to square so axes are equal
    plt.imshow(stars_cropped,aspect = 'equal')
    #plotting asteroid
    #(len(asteroid_x)-1)/2
    if choice == "Add asteroid":
      ax.plot(asteroid_x,asteroid_y, color = 'r',linewidth=0.5) # plot asteroid
      imagebox_asteroid = OffsetImage(Asteroid_img, zoom = 0.03)
      ab_asteroidimg = AnnotationBbox(imagebox_asteroid, [asteroid_x[-1],asteroid_y[-1]], xycoords = 'data', frameon = False)
      ax.add_artist(ab_asteroidimg) # adding image of Earth to last coordinate in path

    ax.plot(earth_x,earth_y, color = 'b',linewidth = 0.5) # plot Earth
    imagebox_earth = OffsetImage(Earth_img, zoom = 0.03)
    ab_earthimg = AnnotationBbox(imagebox_earth, [earth_x[-1],earth_y[-1]], xycoords = 'data', frameon = False)
    ax.add_artist(ab_earthimg)
    
    #plotting sun 
    ax.scatter(sun_scaledx,sun_scaledy, color = 'tab:orange' , s = 1) # plot sun position
    imagebox_sun = OffsetImage(Sun_img, zoom = 0.09)
    ab_sunimg = AnnotationBbox(imagebox_sun, [sun_scaledx, sun_scaledy], xycoords = 'data', frameon = False)
    ax.add_artist(ab_sunimg)    
      
    # changing limits/labels for axes
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.xlabel("Distance [AU]")
    plt.ylabel("Distance [AU]")
    plt.xticks(oldx,AU) # changing the axes so that they display the distance in AU
    plt.yticks(oldy,AU)
    plt.show()
    
    st.pyplot(fig=None, clear_figure=None)
    st.set_option('deprecation.showPyplotGlobalUse', False)
    
main()



