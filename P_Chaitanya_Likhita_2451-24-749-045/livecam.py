"""
ImageShield Live Camera Module.

Provides a small Tkinter camera window that streams from the system webcam,
captures a frame to a temporary PNG file, and returns that file to the main
encryption workflow.
"""

import os
import tempfile
from datetime import datetime

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

try:
	import cv2
except Exception:
	cv2 = None


class LiveCameraWindow:
	"""Live webcam preview window for capturing an image."""

	def __init__(self, parent, on_capture=None, camera_index=0):
		self.parent = parent
		self.on_capture = on_capture
		self.camera_index = camera_index
		self.window = None
		self.cap = None
		self.available_camera_index = None
		if cv2 is None:
			self._show_unavailable_window(
				"OpenCV is not installed, so the live camera feature cannot be used."
			)
			return
		self.cap = self._open_camera(camera_index)
		self.current_frame = None
		self.current_photo = None
		self.captured_path = None
		self.active = False

		if not self.cap.isOpened():
			self.cap.release()
			self._show_unavailable_window(
				"Unable to access the camera. Try a different camera index or check that a webcam is connected and not in use."
			)
			return

		self.window = tk.Toplevel(parent)
		self.window.title("ImageShield Camera Capture")
		self.window.geometry("900x700")
		self.window.configure(bg="#1e1e2e")
		self.window.protocol("WM_DELETE_WINDOW", self.close)
		self.window.resizable(True, True)

		self.video_label = tk.Label(
			self.window,
			text="Starting camera...",
			bg="#0f172a",
			fg="#ffffff",
			relief=tk.SUNKEN,
			width=800,
			height=520
		)
		self.video_label.pack(fill=tk.BOTH, expand=True, padx=16, pady=(16, 10))

		self.status_label = tk.Label(
			self.window,
			text="Live camera ready. Capture a frame to send it back to ImageShield.",
			bg="#1e1e2e",
			fg="#b0b0b0",
			font=("Arial", 10)
		)
		self.status_label.pack(anchor="w", padx=16, pady=(0, 10))

		button_frame = tk.Frame(self.window, bg="#1e1e2e")
		button_frame.pack(fill=tk.X, padx=16, pady=(0, 16))

		self.capture_button = tk.Button(
			button_frame,
			text="Capture Frame",
			command=self.capture_frame,
			bg="#06a77d",
			fg="#ffffff",
			font=("Arial", 10, "bold"),
			padx=14,
			pady=8,
			relief=tk.FLAT,
			cursor="hand2"
		)
		self.capture_button.pack(side=tk.LEFT)

		self.use_button = tk.Button(
			button_frame,
			text="Use Captured Image",
			command=self.use_captured_image,
			bg="#0d7377",
			fg="#ffffff",
			font=("Arial", 10, "bold"),
			padx=14,
			pady=8,
			relief=tk.FLAT,
			cursor="hand2"
		)
		self.use_button.pack(side=tk.LEFT, padx=10)

		self.close_button = tk.Button(
			button_frame,
			text="Close",
			command=self.close,
			bg="#d62828",
			fg="#ffffff",
			font=("Arial", 10, "bold"),
			padx=14,
			pady=8,
			relief=tk.FLAT,
			cursor="hand2"
		)
		self.close_button.pack(side=tk.RIGHT)

		self.active = True
		self._update_frame()

	def _open_camera(self, preferred_index=0):
		"""Try the preferred camera index first, then fall back to other indices."""
		candidate_indices = [preferred_index, 1, 2, 3, 4]
		seen_indices = []

		for index in candidate_indices:
			if index in seen_indices:
				continue
			seen_indices.append(index)
			capture = cv2.VideoCapture(index)
			if capture.isOpened():
				self.available_camera_index = index
				return capture
			capture.release()

		return cv2.VideoCapture(preferred_index)

	def _update_frame(self):
		"""Refresh the live webcam frame."""
		if not self.active:
			return

		if not self.cap.isOpened():
			self.status_label.config(text="Camera disconnected.", fg="#d62828")
			self.window.after(200, self.close)
			return

		ok, frame = self.cap.read()
		if not ok:
			self.status_label.config(text="Unable to read from camera.", fg="#d62828")
			self.window.after(60, self._update_frame)
			return

		self.current_frame = frame
		rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		image = Image.fromarray(rgb_frame)
		image.thumbnail((840, 520))
		self.current_photo = ImageTk.PhotoImage(image)
		self.video_label.config(image=self.current_photo, text="")
		self.video_label.image = self.current_photo

		if not self.captured_path:
			self.status_label.config(
				text="Live preview running. Click Capture Frame when the image looks right.",
				fg="#b0b0b0"
			)

		self.window.after(30, self._update_frame)

	def capture_frame(self):
		"""Save the current camera frame to a temporary PNG file."""
		if self.current_frame is None:
			messagebox.showerror("Camera Error", "No camera frame is available yet.")
			return

		rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
		image = Image.fromarray(rgb_frame)

		temp_name = f"imageshield_camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
		temp_path = os.path.join(tempfile.gettempdir(), temp_name)
		image.save(temp_path, format="PNG")

		self.captured_path = temp_path
		self.status_label.config(
			text=f"Captured image saved to {temp_path}",
			fg="#06a77d"
		)

	def use_captured_image(self):
		"""Return the captured image to the main application."""
		if self.captured_path is None:
			self.capture_frame()

		if self.captured_path is None:
			return

		if self.on_capture:
			self.on_capture(self.captured_path, source_label="Camera")

		self.close()

	def close(self):
		"""Release the camera and close the window."""
		self.active = False

		if hasattr(self, "cap") and self.cap is not None:
			if self.cap.isOpened():
				self.cap.release()

		if hasattr(self, "window") and self.window.winfo_exists():
			self.window.destroy()

	def _show_unavailable_window(self, message):
		"""Show a non-modal fallback window when camera access is unavailable."""
		self.window = tk.Toplevel(self.parent)
		self.window.title("ImageShield Camera Capture")
		self.window.geometry("700x260")
		self.window.configure(bg="#1e1e2e")
		self.window.protocol("WM_DELETE_WINDOW", self.close)
		self.window.resizable(False, False)

		container = tk.Frame(self.window, bg="#1e1e2e")
		container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

		title_label = tk.Label(
			container,
			text="Camera unavailable",
			bg="#1e1e2e",
			fg="#ffffff",
			font=("Arial", 14, "bold")
		)
		title_label.pack(anchor="w", pady=(0, 10))

		message_label = tk.Label(
			container,
			text=message,
			bg="#1e1e2e",
			fg="#b0b0b0",
			font=("Arial", 10),
			justify="left",
			wraplength=640
		)
		message_label.pack(anchor="w", pady=(0, 16))

		if self.available_camera_index is not None:
			index_label = tk.Label(
				container,
				text=f"Camera index in use: {self.available_camera_index}",
				bg="#1e1e2e",
				fg="#06a77d",
				font=("Arial", 10, "bold")
			)
			index_label.pack(anchor="w", pady=(0, 12))

		button_row = tk.Frame(container, bg="#1e1e2e")
		button_row.pack(fill=tk.X)

		close_button = tk.Button(
			button_row,
			text="Close",
			command=self.close,
			bg="#d62828",
			fg="#ffffff",
			font=("Arial", 10, "bold"),
			padx=14,
			pady=8,
			relief=tk.FLAT,
			cursor="hand2"
		)
		close_button.pack(side=tk.RIGHT)


def launch_camera(parent, on_capture=None):
	"""Open the live camera capture window."""
	return LiveCameraWindow(parent, on_capture=on_capture)
