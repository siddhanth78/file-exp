import pygame, sys
from pygame.locals import *

pygame.init()

class FieldBox(pygame.sprite.Sprite):
	def __init__(self, x, y, entry_color=(0,0,0), text_color=(0,0,0), max_chars=15, sysfont="Courier", font=None):
		self.x = x
		self.y = y
		self.text_in = ''
		self.max_chars = max_chars
		self.rect = Rect(x-5, y-5, 12*(max_chars+1), 30)
		self.active = False
		self.cursorx = x
		self.cursory = y
		self.entry_color = entry_color
		self.text_color = text_color
		self.cursor_index = 0
		self.hide = False
		if font == None:
			self.font_ = pygame.font.SysFont(sysfont, 20)
		else:
			self.font_ = pygame.font.Font(font, 20)

	def render(self, screen):
		if self.hide == False:
			if self.active == True:
				pygame.draw.rect(screen, self.entry_color, self.rect, 3, 3)
				pygame.draw.line(screen, self.text_color, (self.cursorx, self.cursory), (self.cursorx, self.cursory+20), 3)
			else:
				pygame.draw.rect(screen, self.entry_color, self.rect, 1, 3)
		
			txt_surf = self.font_.render(self.text_in, True, self.text_color)
			screen.blit(txt_surf, (self.x, self.y))

	def set_active(self):
		self.active = True

	def show_box(self):
		self.hide = False

	def hide_box(self):
		self.hide = True

	def is_hidden(self):
		return self.hide

	def move_cursorx(self, x_):
		x_ = x_ * 12
		if self.cursorx + x_ < self.x:
			self.cursorx = self.x
			self.cursor_index = 0
		elif self.cursorx + x_ > self.x + (len(self.text_in))*12:
			self.cursorx = self.x + (len(self.text_in))*12
			self.cursor_index = len(self.text_in)
		elif self.cursorx + x_ > self.x + (self.max_chars)*12:
			self.cursorx = self.x + (self.max_chars)*12
			self.cursor_index = self.max_chars
		else:
			self.cursorx += x_
			self.cursor_index += (x_//12)

	def get_cursorx(self):
		return self.cursorx 

	def set_inactive(self):
		self.active = False

	def is_active(self):
		return self.active

	def get_rect(self):
		return self.rect

	def set_text(self, text):
		if len(text) <= self.max_chars:
			self.text_in = text
			self.cursorx = self.x + 12*len(text)
			self.cursor_index = len(text)

	def remove_behind_cursor(self):
		if self.cursor_index > 0:
			self.text_in = self.text_in[:self.cursor_index-1] + self.text_in[self.cursor_index:]
			self.cursorx -= 12
			self.cursor_index -= 1

	def get_text(self):
		return self.text_in

	def append_char(self, c):
		if len(self.text_in + c) <= self.max_chars:
			self.text_in += c
			self.move_cursorx(1)

	def append_text(self, w):
		if len(self.text_in + w) <= self.max_chars:
			self.text_in += w
			self.move_cursorx(len(w))

	def append_at_cursor(self, w):
		if len(self.text_in[:self.cursor_index] + w + self.text_in[self.cursor_index:]) <= self.max_chars:
			self.text_in = self.text_in[:self.cursor_index] + w + self.text_in[self.cursor_index:]
			self.move_cursorx(len(w))

	def get_max_chars(self):
		return self.max_chars
