from fieldBox import FieldBox
import pygame, sys
from pygame.locals import *
import os

pygame.init()

screen = pygame.display.set_mode((1000, 750))
clock = pygame.time.Clock()
pygame.key.set_repeat(250, 25)

entry = FieldBox(50, 50, entry_color=(255,255,255), text_color=(255,255,255), max_chars=75)

suggestions = []
curr_sug = 0

cmds = ["!new-folder", "!delete-file", "!tag-add", "!tag-remove", "!rename", "!refresh", "!tag-remove-all"]
vars_ = []

def get_dirs_and_files(root):
	for en in os.scandir(root):
		try:
			if en.is_file(follow_symlinks=False):
				yield en.name
			elif en.is_dir(follow_symlinks=False):
				yield en.name
				yield from get_dirs_and_files(en.path)
		except:
			pass

def initial_setup(root, cmds, vars_):
	tagged = os.path.join(root, "My Tagged Files")
	if os.path.exists(tagged) == False:
		os.mkdir(tagged)
		image_tagged = os.path.join(tagged, "#img")
		os.mkdir(image_tagged)
		files_tagged = os.path.join(tagged, "#file")
		os.mkdir(files_tagged)
		misc_tagged = os.path.join(tagged, "#misc")
		os.mkdir(misc_tagged)
		no_tag = os.path.join(tagged, "No Tags")
		os.mkdir(no_tag)
	
	tags = [path for path in get_dirs_and_files(tagged)]
	tags.extend(cmds)
	tags.extend(vars_)
	curr_path = tagged
	return tags, curr_path

print("Initializing...")
tags, curr_path = initial_setup(os.path.expanduser("~"), cmds, vars_)

class TrieNode:
	def __init__(self):
		self.children = {}
		self.is_end_of_word = False

class Trie:
	def __init__(self):
		self.root = TrieNode()
		self.has_empty_string = False

	def insert(self, word):
		if word == "":
			self.has_empty_string = True
			return

		node = self.root
		for char in word:
			if char not in node.children:
				node.children[char] = TrieNode()
			node = node.children[char]
		node.is_end_of_word = True

	def remove(self, word):
		if word == "":
			self.has_empty_string = False
			return

		def _remove(node, word, depth):
			if depth == len(word):
				if node.is_end_of_word:
					node.is_end_of_word = False
				return len(node.children) == 0 and not node.is_end_of_word

			char = word[depth]
			if char not in node.children:
				return False

			should_delete_current_node = _remove(node.children[char], word, depth + 1)

			if should_delete_current_node:
				del node.children[char]
				return len(node.children) == 0 and not node.is_end_of_word
			return False

		_remove(self.root, word, 0)

	def find_prefix(self, prefix):
		if prefix == "":
			return [""] if self.has_empty_string else []

		node = self.root
		for char in prefix:
			if char not in node.children:
				return []
			node = node.children[char]
		return self._words_with_prefix(node, prefix)

	def _words_with_prefix(self, node, prefix):
		results = []
		if node.is_end_of_word:
			results.append(prefix)

		for char, child_node in node.children.items():
			results.extend(self._words_with_prefix(child_node, prefix + char))

		return results

tab_tree = Trie()

if tags:
	for t in tags:
		if t:
			tab_tree.insert(t)

font_ = pygame.font.SysFont("Courier", 20)

while True:
	screen.fill((0,0,0))
	entry.render(screen)
	curr_path_surf = font_.render(curr_path, True, (255,255,255))
	screen.blit(curr_path_surf, (50, 80))
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			sys.exit(0)
		elif event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:
				if entry.get_rect().collidepoint(event.pos) and entry.is_active() == False:
					entry.set_active()
				else:
					entry.set_inactive()
		elif event.type == pygame.KEYDOWN:
			if entry.is_active() == True and entry.is_hidden() == False:
				if event.key == pygame.K_BACKSPACE:
					entry.remove_behind_cursor()
					suggestions = tab_tree.find_prefix(entry.get_text())
					suggestions.sort()
					suggestions = suggestions[:10]
					curr_sug = 0
				elif event.key == pygame.K_RETURN:
					command = entry.get_text()
				elif event.key == pygame.K_LEFT:
					entry.move_cursorx(-1)
				elif event.key == pygame.K_RIGHT:
					entry.move_cursorx(1)
				elif event.key == pygame.K_TAB:
					if suggestions:
						entry.set_text(suggestions[curr_sug])
						curr_sug = (curr_sug+1)%len(suggestions)
					else:
						curr_sug = 0
				elif event.unicode:
					entry.append_at_cursor(event.unicode)
					suggestions = tab_tree.find_prefix(entry.get_text())
					suggestions.sort()
					suggestions = suggestions[:10]
					curr_sug = 0

	pygame.display.update()
	clock.tick(30)
