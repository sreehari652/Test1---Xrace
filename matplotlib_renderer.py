"""
UWB Racing Tracker - Matplotlib Renderer Module
Handles all visualization using matplotlib instead of pygame
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import numpy as np
import time
import math
from config import *
from race_config import *


class MatplotlibRenderer:
    """Renders UWB tracking using matplotlib"""
    
    def __init__(self, scale_params):
        """
        Initialize matplotlib renderer
        
        Args:
            scale_params: Dictionary with scaling parameters
        """
        self.cm2p = scale_params['cm2p']
        self.x_offset = scale_params['x_offset']
        self.y_offset = scale_params['y_offset']
        
        # Create figure and axes
        self.fig, self.ax = plt.subplots(figsize=(14, 9))
        self.fig.canvas.manager.set_window_title('UWB Racing Tracker')
        
        # Set up the plot
        self.ax.set_xlim(0, SCREEN_X)
        self.ax.set_ylim(0, SCREEN_Y)
        self.ax.set_aspect('equal')
        self.ax.invert_yaxis()  # Invert Y to match pygame coordinates
        
        # Remove axes for cleaner look
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Enable interactive mode
        plt.ion()
        plt.show(block=False)
    
    def cm_to_pixels(self, x_cm, y_cm):
        """Convert cm coordinates to pixel coordinates"""
        pixel_x = x_cm * self.cm2p + self.x_offset
        pixel_y = SCREEN_Y - (y_cm * self.cm2p + self.y_offset)
        return pixel_x, pixel_y
    
    def draw_grid(self):
        """Draw background grid"""
        grid_spacing = GRID_SPACING_CM * self.cm2p
        
        for x in np.arange(0, SCREEN_X, grid_spacing):
            self.ax.axvline(x, color='lightgray', linewidth=0.5, alpha=0.5)
        
        for y in np.arange(0, SCREEN_Y, grid_spacing):
            self.ax.axhline(y, color='lightgray', linewidth=0.5, alpha=0.5)
    
    def draw_tracking_area(self, anchors):
        """Draw the tracking area boundary"""
        if len(anchors) < 3:
            return
        
        corner_points = []
        for anchor in anchors:
            px, py = self.cm_to_pixels(anchor.x, anchor.y)
            corner_points.append([px, py])
        
        if len(corner_points) >= 3:
            polygon = patches.Polygon(corner_points, fill=False, 
                                     edgecolor='blue', linewidth=2)
            self.ax.add_patch(polygon)
    
    def draw_start_line(self):
        """Draw the start/finish line"""
        if not SHOW_START_LINE:
            return
        
        if START_LINE_ORIENTATION == 'vertical':
            x_pixel, y1_pixel = self.cm_to_pixels(START_LINE_X, START_LINE_Y1)
            _, y2_pixel = self.cm_to_pixels(START_LINE_X, START_LINE_Y2)
            
            self.ax.plot([x_pixel, x_pixel], [y1_pixel, y2_pixel], 
                        color='green', linewidth=4, label='START/FINISH')
            
            self.ax.text(x_pixel + 10, y1_pixel + 10, 'START/FINISH',
                        fontsize=12, color='green', fontweight='bold')
            
        else:  # horizontal
            x1_pixel, y_pixel = self.cm_to_pixels(START_LINE_X1, START_LINE_Y)
            x2_pixel, _ = self.cm_to_pixels(START_LINE_X2, START_LINE_Y)
            
            self.ax.plot([x1_pixel, x2_pixel], [y_pixel, y_pixel],
                        color='green', linewidth=4, label='START/FINISH')
            
            self.ax.text(x1_pixel + 10, y_pixel - 25, 'START/FINISH',
                        fontsize=12, color='green', fontweight='bold')
    
    def draw_anchor(self, anchor):
        """Draw an anchor device"""
        pixel_x, pixel_y = self.cm_to_pixels(anchor.x, anchor.y)
        
        circle = plt.Circle((pixel_x, pixel_y), ANCHOR_RADIUS, 
                           color='black', zorder=5)
        self.ax.add_patch(circle)
        
        label_text = f"{anchor.name}\n({anchor.x},{anchor.y})"
        self.ax.text(pixel_x + 12, pixel_y - 8, label_text,
                    fontsize=8, color='black')
    
    def draw_tag_trail(self, tag):
        """Draw position history trail for a tag"""
        if len(tag.history) < 2:
            return
        
        points_x = []
        points_y = []
        
        for hx, hy, ht in tag.history:
            px, py = self.cm_to_pixels(hx, hy)
            points_x.append(px)
            points_y.append(py)
        
        self.ax.plot(points_x, points_y, 'y-', linewidth=2, alpha=0.5)
    
    def get_quality_color(self, quality):
        """Get color based on quality level"""
        quality_colors = {
            "excellent": 'green',
            "good": 'blue',
            "fair": 'orange',
            "poor": 'red',
            "unknown": 'gray'
        }
        return quality_colors.get(quality, 'gray')
    
    def draw_tag(self, tag, lap_info=None, speed_info=None, collision_info=None):
        """Draw a tag device with racing info"""
        pixel_x, pixel_y = self.cm_to_pixels(tag.x, tag.y)
        
        color = self.get_quality_color(tag.quality)
        
        # Draw trail
        self.draw_tag_trail(tag)
        
        # Draw tag circle
        circle = plt.Circle((pixel_x, pixel_y), TAG_RADIUS, 
                           color=color, zorder=10)
        self.ax.add_patch(circle)
        
        # Collision indicator
        if collision_info and collision_info.get('is_in_collision', False):
            collision_circle = plt.Circle((pixel_x, pixel_y), COLLISION_INDICATOR_RADIUS,
                                         fill=False, edgecolor='red', linewidth=3, zorder=11)
            self.ax.add_patch(collision_circle)
        
        # Build label text
        label_lines = [f"{tag.name} ({int(tag.x)},{int(tag.y)})"]
        
        if lap_info:
            if lap_info['is_racing']:
                label_lines.append(f"Lap {lap_info['current_lap']}/{lap_info['total_laps']}")
            elif lap_info['race_finished']:
                label_lines.append("FINISHED")
        
        if speed_info:
            if SPEED_CALC_METHOD == 'both':
                speed_text = f"S: {speed_info['instantaneous']:.1f} (Avg: {speed_info['average']:.1f})"
            elif SPEED_CALC_METHOD == 'instantaneous':
                speed_text = f"S: {speed_info['instantaneous']:.1f}"
            else:
                speed_text = f"S: {speed_info['average']:.1f}"
            label_lines.append(speed_text)
        
        label_text = '\n'.join(label_lines)
        self.ax.text(pixel_x + 18, pixel_y, label_text,
                    fontsize=8, color=color, verticalalignment='top')
    
    def draw_leaderboard(self, race_manager, collision_detector):
        """Draw race leaderboard"""
        x_pos = LEADERBOARD_X
        y_pos = LEADERBOARD_Y
        
        leaderboard = race_manager.get_leaderboard()
        
        lines = ["LEADERBOARD", "=" * 40]
        lines.append("Pos  Car       Lap    Time    Points")
        lines.append("-" * 40)
        
        for idx, car_info in enumerate(leaderboard):
            position = idx + 1
            car_name = car_info['car_name']
            current_lap = car_info['current_lap']
            total_laps = car_info['total_laps']
            total_time = car_info['total_time']
            
            collision_info = collision_detector.get_car_collision_info(car_info['car_id'])
            points = collision_info['points'] if collision_info else 0
            
            if car_info['race_finished']:
                lap_str = "FIN"
            else:
                lap_str = f"{current_lap}/{total_laps}"
            
            line = f"{position}.   {car_name}    {lap_str:6}  {total_time:6.1f}s  {points:+4d}"
            lines.append(line)
        
        lines.append("")
        lines.append("COLLISIONS")
        lines.append("-" * 40)
        
        for car_info in leaderboard:
            collision_info = collision_detector.get_car_collision_info(car_info['car_id'])
            if collision_info:
                line = (f"{collision_info['car_name']}: {collision_info['total_collisions']} "
                       f"(Init: {collision_info['initiated']}, Recv: {collision_info['received']})")
                lines.append(line)
        
        leaderboard_text = '\n'.join(lines)
        self.ax.text(x_pos, y_pos, leaderboard_text,
                    fontsize=9, family='monospace',
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    def draw_race_status(self, race_manager):
        """Draw overall race status"""
        x_pos = RACE_STATUS_X
        y_pos = RACE_STATUS_Y
        
        if race_manager.is_race_active():
            status_text = "RACE IN PROGRESS"
            
            if race_manager.race_start_time:
                elapsed = time.time() - race_manager.race_start_time
                status_text += f"\nTime: {elapsed:.1f}s"
        else:
            status_text = "WAITING FOR RACE START"
        
        self.ax.text(x_pos, y_pos, status_text,
                    fontsize=12, fontweight='bold',
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    def render_frame(self, anchors, tags, race_manager, speed_manager, 
                    collision_detector, show_debug=False):
        """Render complete racing frame"""
        # Clear previous frame
        self.ax.clear()
        self.ax.set_xlim(0, SCREEN_X)
        self.ax.set_ylim(0, SCREEN_Y)
        self.ax.set_aspect('equal')
        self.ax.invert_yaxis()
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Draw elements
        self.draw_grid()
        self.draw_tracking_area(anchors)
        self.draw_start_line()
        
        for anchor in anchors:
            self.draw_anchor(anchor)
        
        for tag in tags:
            if tag.status and tag.is_active(TAG_TIMEOUT):
                lap_info = race_manager.get_car_lap_info(tag.id)
                speed_info = speed_manager.get_car_speed_info(tag.id)
                collision_info = collision_detector.get_car_collision_info(tag.id)
                
                self.draw_tag(tag, lap_info, speed_info, collision_info)
        
        self.draw_race_status(race_manager)
        self.draw_leaderboard(race_manager, collision_detector)
        
        # Refresh display
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)
    
    def close(self):
        """Close the matplotlib window"""
        plt.close(self.fig)
