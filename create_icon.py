#!/usr/bin/env python3
"""
Create a notification bell icon for the Superset Post Monitor
"""

from PIL import Image, ImageDraw
import os

def create_notification_bell_icon():
    """Create a simple notification bell icon"""
    # Create a 64x64 image with transparent background
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Bell body (main part)
    bell_color = (52, 152, 219, 255)  # Blue color
    bell_x1, bell_y1 = size//4, size//3
    bell_x2, bell_y2 = size*3//4, size*2//3
    
    # Draw bell shape (ellipse for simplicity)
    draw.ellipse([bell_x1, bell_y1, bell_x2, bell_y2], fill=bell_color, outline=(41, 128, 185, 255), width=2)
    
    # Bell top (small rectangle)
    top_x1, top_y1 = size//2 - 3, bell_y1 - 8
    top_x2, top_y2 = size//2 + 3, bell_y1
    draw.rectangle([top_x1, top_y1, top_x2, top_y2], fill=bell_color)
    
    # Bell clapper (small circle)
    clapper_x = size//2
    clapper_y = bell_y2 - 8
    clapper_radius = 3
    draw.ellipse([clapper_x - clapper_radius, clapper_y - clapper_radius, 
                  clapper_x + clapper_radius, clapper_y + clapper_radius], 
                 fill=(231, 76, 60, 255))  # Red clapper
    
    # Notification dot (small red circle in top-right)
    dot_x, dot_y = size*3//4 + 5, size//4 - 5
    dot_radius = 6
    draw.ellipse([dot_x - dot_radius, dot_y - dot_radius, 
                  dot_x + dot_radius, dot_y + dot_radius], 
                 fill=(231, 76, 60, 255))  # Red notification dot
    
    # Add a subtle shadow/glow effect
    shadow_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    
    # Shadow bell (slightly offset)
    shadow_offset = 2
    shadow_draw.ellipse([bell_x1 + shadow_offset, bell_y1 + shadow_offset, 
                        bell_x2 + shadow_offset, bell_y2 + shadow_offset], 
                       fill=(0, 0, 0, 50))  # Semi-transparent black shadow
    
    # Combine shadow and main image
    final_img = Image.alpha_composite(shadow_img, img)
    
    return final_img

if __name__ == "__main__":
    try:
        # Create the icon
        icon = create_notification_bell_icon()
        
        # Save as PNG
        icon.save('notification-bell.png', 'PNG')
        print("✅ Created notification-bell.png successfully!")
        
        # Also create different sizes for better compatibility
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
        
        # Create ICO file with multiple sizes
        icon.save('notification-bell.ico', format='ICO', sizes=sizes)
        print("✅ Created notification-bell.ico successfully!")
        
        print("🎨 Icon files created:")
        print("   - notification-bell.png (main icon)")
        print("   - notification-bell.ico (Windows icon)")
        
    except ImportError:
        print("❌ Pillow library not found. Install it with: pip install Pillow")
    except Exception as e:
        print(f"❌ Error creating icon: {e}")