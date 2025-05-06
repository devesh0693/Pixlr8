import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import numpy as np
from threading import Thread
import tempfile

class PixelateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pixelate Art Creator")
        self.root.geometry("1000x700")
        
        # Set appearance mode and default color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Variables
        self.original_image = None
        self.processed_image = None
        self.original_cv_image = None
        self.current_file_path = None
        self.is_video = False
        self.video_frames = []
        self.current_frame_index = 0
        self.temp_dir = tempfile.mkdtemp()
        
        # Main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel (controls)
        self.control_panel = ctk.CTkFrame(self.main_frame, width=200)
        self.control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # Title
        self.title_label = ctk.CTkLabel(self.control_panel, text="Pixelate Art Creator", 
                                        font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=20)
        
        # Open file button
        self.open_button = ctk.CTkButton(self.control_panel, text="Open File", command=self.open_file)
        self.open_button.pack(pady=10, padx=20, fill=tk.X)
        
        # Pixelation control
        self.pixel_size_label = ctk.CTkLabel(self.control_panel, text="Pixel Size")
        self.pixel_size_label.pack(pady=(20, 5))
        
        self.pixel_size_slider = ctk.CTkSlider(self.control_panel, from_=5, to=50, 
                                              command=self.update_preview)
        self.pixel_size_slider.set(20)
        self.pixel_size_slider.pack(pady=5, padx=20, fill=tk.X)
        
        self.pixel_size_value = ctk.CTkLabel(self.control_panel, text="20")
        self.pixel_size_value.pack(pady=5)
        
        # Color reduction control
        self.color_reduction_label = ctk.CTkLabel(self.control_panel, text="Color Reduction")
        self.color_reduction_label.pack(pady=(20, 5))
        
        self.color_reduction_slider = ctk.CTkSlider(self.control_panel, from_=2, to=64, 
                                                  command=self.update_preview)
        self.color_reduction_slider.set(16)
        self.color_reduction_slider.pack(pady=5, padx=20, fill=tk.X)
        
        self.color_reduction_value = ctk.CTkLabel(self.control_panel, text="16")
        self.color_reduction_value.pack(pady=5)
        
        # Contrast enhancement
        self.contrast_label = ctk.CTkLabel(self.control_panel, text="Contrast Enhancement")
        self.contrast_label.pack(pady=(20, 5))
        
        self.contrast_slider = ctk.CTkSlider(self.control_panel, from_=0.5, to=2.0, 
                                           command=self.update_preview)
        self.contrast_slider.set(1.0)
        self.contrast_slider.pack(pady=5, padx=20, fill=tk.X)
        
        self.contrast_value = ctk.CTkLabel(self.control_panel, text="1.0")
        self.contrast_value.pack(pady=5)
        
        # Video controls (initially hidden)
        self.video_controls_frame = ctk.CTkFrame(self.control_panel)
        
        self.prev_frame_button = ctk.CTkButton(self.video_controls_frame, text="Previous Frame", 
                                              command=self.prev_frame)
        self.prev_frame_button.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.X, expand=True)
        
        self.next_frame_button = ctk.CTkButton(self.video_controls_frame, text="Next Frame", 
                                              command=self.next_frame)
        self.next_frame_button.pack(side=tk.RIGHT, padx=5, pady=10, fill=tk.X, expand=True)
        
        # Save button
        self.save_button = ctk.CTkButton(self.control_panel, text="Save Image", command=self.save_image)
        self.save_button.pack(pady=(30, 10), padx=20, fill=tk.X)
        
        # Right panel (image display)
        self.image_frame = ctk.CTkFrame(self.main_frame)
        self.image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.image_frame, bg="#2a2d2e", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = ctk.CTkLabel(self.root, text="Ready", anchor="w")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Initial message
        self.display_welcome_message()
    
    def display_welcome_message(self):
        welcome_text = "Welcome to Pixelate Art Creator\n\nOpen an image or video file to start"
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_reqwidth() // 2, 
            self.canvas.winfo_reqheight() // 2,
            text=welcome_text, 
            fill="white", 
            font=("Helvetica", 16),
            justify=tk.CENTER
        )
    
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image & Video Files", "*.png *.jpg *.jpeg *.gif *.mp4"),
                ("Image Files", "*.png *.jpg *.jpeg *.gif"),
                ("Video Files", "*.mp4"),
                ("All Files", "*.*"),
            ]
        )
        
        if not file_path:
            return
        
        self.current_file_path = file_path
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.mp4':
            # Handle video file
            self.is_video = True
            self.video_controls_frame.pack(pady=10, padx=20, fill=tk.X)
            self.status_bar.configure(text="Processing video frames... Please wait.")
            self.root.update()
            
            # Extract frames in a separate thread to keep UI responsive
            thread = Thread(target=self.extract_video_frames, args=(file_path,))
            thread.daemon = True
            thread.start()
        else:
            # Handle image file
            self.is_video = False
            self.video_controls_frame.pack_forget()
            self.load_image(file_path)
            self.update_preview()
    
    def extract_video_frames(self, video_path):
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            # Only extract key frames or a maximum number of frames
            max_frames = min(total_frames, 20)  # Limit to 20 frames
            step = max(1, total_frames // max_frames)
            
            self.video_frames = []
            current_frame = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if current_frame % step == 0:
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.video_frames.append(rgb_frame)
                
                current_frame += 1
                
                # Update status periodically
                if current_frame % 10 == 0:
                    progress = min(100, int((current_frame / total_frames) * 100))
                    self.status_bar.configure(text=f"Processing video: {progress}% complete")
                    self.root.update()
            
            cap.release()
            
            if self.video_frames:
                self.current_frame_index = 0
                self.original_cv_image = self.video_frames[0]
                self.original_image = Image.fromarray(self.original_cv_image)
                self.status_bar.configure(text=f"Video loaded: {len(self.video_frames)} frames extracted")
                self.update_preview()
            else:
                messagebox.showerror("Error", "Failed to extract frames from video.")
                self.status_bar.configure(text="Error processing video.")
        except Exception as e:
            messagebox.showerror("Error", f"Error processing video: {str(e)}")
            self.status_bar.configure(text="Error processing video.")
    
    def load_image(self, image_path):
        try:
            if image_path.lower().endswith('.gif'):
                # For GIF, just take the first frame
                self.original_image = Image.open(image_path).convert('RGB')
                self.original_cv_image = np.array(self.original_image)
            else:
                # For other formats
                self.original_cv_image = cv2.imread(image_path)
                self.original_cv_image = cv2.cvtColor(self.original_cv_image, cv2.COLOR_BGR2RGB)
                self.original_image = Image.fromarray(self.original_cv_image)
            
            self.status_bar.configure(text=f"Loaded: {os.path.basename(image_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open the image: {str(e)}")
            self.status_bar.configure(text="Error loading image.")
    
    def pixelate_image(self, image, pixel_size, color_reduction, contrast):
        try:
            # Create a copy of the original
            img = image.copy()
            
            # Apply contrast enhancement
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(contrast)
            
            # Get original dimensions
            width, height = img.size
            
            # Resize down
            small_img = img.resize((width // pixel_size, height // pixel_size), Image.LANCZOS)
            
            # Apply color reduction
            if color_reduction > 0:
                small_img = small_img.convert('P', palette=Image.ADAPTIVE, colors=int(color_reduction))
                small_img = small_img.convert('RGB')
            
            # Resize up to create pixelation effect
            result = small_img.resize((width, height), Image.NEAREST)
            
            return result
        except Exception as e:
            messagebox.showerror("Error", f"Error during pixelation: {str(e)}")
            return image
    
    def update_preview(self, *args):
        if self.original_image is None:
            return
        
        # Get current values from sliders
        pixel_size = int(self.pixel_size_slider.get())
        color_reduction = int(self.color_reduction_slider.get())
        contrast = self.contrast_slider.get()
        
        # Update value labels
        self.pixel_size_value.configure(text=str(pixel_size))
        self.color_reduction_value.configure(text=str(color_reduction))
        self.contrast_value.configure(text=f"{contrast:.1f}")
        
        # Process the image
        if self.is_video:
            current_frame = self.video_frames[self.current_frame_index]
            current_image = Image.fromarray(current_frame)
        else:
            current_image = self.original_image
        
        # Actually pixelate the image
        self.processed_image = self.pixelate_image(current_image, pixel_size, color_reduction, contrast)
        
        # Display the processed image
        self.display_image(self.processed_image)
        
        # Update status
        if self.is_video:
            self.status_bar.configure(text=f"Frame {self.current_frame_index + 1}/{len(self.video_frames)}")
        else:
            self.status_bar.configure(text="Preview updated")
    
    def display_image(self, image):
        # Clear the canvas
        self.canvas.delete("all")
        
        # Get the canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not yet fully initialized, try again after a short delay
            self.root.after(100, lambda: self.display_image(image))
            return
        
        # Get image dimensions
        img_width, img_height = image.size
        
        # Calculate scaling to fit in canvas while preserving aspect ratio
        scale_width = canvas_width / img_width
        scale_height = canvas_height / img_height
        scale = min(scale_width, scale_height)
        
        # New dimensions
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize the image to fit the canvas
        display_image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to PhotoImage for Canvas
        self.tk_image = ImageTk.PhotoImage(display_image)
        
        # Calculate center position
        x_position = (canvas_width - new_width) // 2
        y_position = (canvas_height - new_height) // 2
        
        # Add image to canvas
        self.canvas.create_image(x_position, y_position, anchor=tk.NW, image=self.tk_image)
    
    def prev_frame(self):
        if self.is_video and self.video_frames:
            self.current_frame_index = (self.current_frame_index - 1) % len(self.video_frames)
            self.original_cv_image = self.video_frames[self.current_frame_index]
            self.original_image = Image.fromarray(self.original_cv_image)
            self.update_preview()
    
    def next_frame(self):
        if self.is_video and self.video_frames:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.video_frames)
            self.original_cv_image = self.video_frames[self.current_frame_index]
            self.original_image = Image.fromarray(self.original_cv_image)
            self.update_preview()
    
    def save_image(self):
        if self.processed_image is None:
            messagebox.showinfo("Info", "No image to save.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg"),
                ("All Files", "*.*"),
            ],
        )
        
        if not file_path:
            return
        
        try:
            self.processed_image.save(file_path)
            self.status_bar.configure(text=f"Saved: {os.path.basename(file_path)}")
            messagebox.showinfo("Success", "Image saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving image: {str(e)}")
            self.status_bar.configure(text="Error saving image.")
    
    def cleanup(self):
        # Clean up temp directory if it exists
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                try:
                    os.remove(os.path.join(self.temp_dir, file))
                except:
                    pass
            try:
                os.rmdir(self.temp_dir)
            except:
                pass

# Fix for missing ImageEnhance import
from PIL import ImageEnhance

if __name__ == "__main__":
    root = ctk.CTk()
    app = PixelateApp(root)
    
    # Clean up on close
    root.protocol("WM_DELETE_WINDOW", lambda: [app.cleanup(), root.destroy()])
    
    root.mainloop()