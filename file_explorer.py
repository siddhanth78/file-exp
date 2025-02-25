from fieldBox import FieldBox
import pygame, sys
from pygame.locals import *
import os
import shutil

pygame.init()

screen = pygame.display.set_mode((1000, 750))
clock = pygame.time.Clock()
pygame.key.set_repeat(250, 25)

entry = FieldBox(50, 50, entry_color=(255,255,255), text_color=(255,255,255), max_chars=75)

suggestions = []
curr_sug = 0
tag_dict = {}

cmds = ["!delete-file", "!tag-add", "!tag-remove", "!rename", "!refresh", "!tag-remove-all", "!tag-show"]
vars_ = []

def get_dirs_and_files(root, tag, tag_dict):
    for en in os.scandir(root):
        try:
            if en.is_file(follow_symlinks=False):
                if en.name.lower() != ".ds_store":
                    tag_dict[tag].append(en.name)
                    yield en.name
            elif en.is_dir(follow_symlinks=False):
                tag = en.name
                tag_dict[tag] = []
                yield en.name
                yield from get_dirs_and_files(en.path, tag, tag_dict)
        except:
            pass

def initial_setup(root, cmds, vars_):
	tagged = os.path.join(root, "Documents/My Tagged Files")
	if os.path.exists(tagged) == False:
		os.mkdir(tagged)
		image_tagged = os.path.join(tagged, "#img")
		os.mkdir(image_tagged)
		files_tagged = os.path.join(tagged, "#file")
		os.mkdir(files_tagged)
		misc_tagged = os.path.join(tagged, "#misc")
		os.mkdir(misc_tagged)
		no_tag = os.path.join(tagged, "#untagged")
		os.mkdir(no_tag)
	
	tags = [path for path in get_dirs_and_files(tagged, None, tag_dict)]
	tags.extend(cmds)
	tags.extend(vars_)
	curr_path = tagged
	return tags, curr_path

print("Initializing...")
tags, curr_path = initial_setup(os.path.expanduser("~"), cmds, vars_)

default_path = os.path.join(curr_path, "#untagged")

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

font_ = pygame.font.SysFont("Courier", 10)

def parse_command(command, tag_dict, tags, tab_tree):
    root_dir = os.path.expanduser("~")
    command_list = command.strip().split(">")
    com = command_list[0].strip()
    if com == "!delete-file":
        if "#" in command_list[1]:
            return "Invalid file name", tags, tag_dict, tab_tree
        try:
            for t in tag_dict:
                if command_list[1] in tag_dict[t]:
                    os.remove(os.path.join(root_dir, t, command_list[1]))
                    tag_dict[t].remove(command_list[1])
            tags.remove(command_list[1])
            tab_tree.remove(command_list[1])
            return f"Removed {command_list[1]}", tags, tag_dict, tab_tree
        except OSError:
            return "File not found", tags, tag_dict, tab_tree
        except:
            return "Error deleting file", tags, tag_dict, tab_tree 

    elif com == "!rename":
        if "#" in command_list[1] or "&&" in command_list[1] or "#" in command_list[2] or "&&" in command_list[2]:
            return "Invalid file name", tags, tag_dict, tab_tree
        try:
            for t in tag_dict:
                if command_list[1] in set(tag_dict[t]):
                    os.rename(os.path.join(root_dir, t, command_list[1]), os.path.join(root_dir, t, command_list[2]))
                    tag_dict[t][tag_dict[t].index(command_list[1])] = command_list[2]
            tags[tags.index(command_list[1])] = command_list[2]
            tab_tree.remove(command_list[1])
            tab_tree.insert(command_list[2])
            return f"Renamed {command_list[1]} to {command_list[2]}", tags, tag_dict, tab_tree
        except OSError:
            return "File not found", tags, tag_dict, tab_tree
        except:
            return "Error renaming file", tags, tag_dict, tab_tree

    else:
        if "&&" not in com and "#" not in com:
            try:
                for t in tag_dict:
                    if com in tag_dict[t]:
                        os.system(f"cd '{os.path.join(os.path.expanduser('~'), 'Documents/My Tagged Files')}' && open '{os.path.join(t, com.strip())}'")
                        return f"Opened {com.strip()}", tags, tag_dict, tab_tree
                return "Couldn't open file", tags, tag_dict, tab_tree
            except:
                return "Error opening file", tags, tag_dict, tab_tree

        list_of_tags_or_file = com.strip().split("&&")
        all_files = set()
        for ltf in list_of_tags_or_file:
            ltf = ltf.strip()
            for f in tag_dict[ltf]:
                if f not in all_files:
                    all_files.add(f)
        return "\n".join(list(all_files)), tags, tag_dict, tab_tree

feed_back = ""

while True:
    screen.fill((0,0,0))
    entry.render(screen)
    feed_surf = font_.render(feed_back, True, (255,255,255))
    screen.blit(feed_surf, (50, 80))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            print(tag_dict)
            sys.exit(0)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if entry.get_rect().collidepoint(event.pos) and entry.is_active() == False:
                    entry.set_active()
                else:
                    entry.set_inactive()
        elif event.type == pygame.DROPFILE:
            file_path = event.file
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            if "#" in file_name or "&&" in file_name:
                feed_back = "Invalid file name"
            else:
                if os.path.exists(os.path.join(default_path, file_name)) == False:
                    new_file_name = file_name.replace(" ", "_")
                    shutil.move(file_path, default_path)
                    os.rename(os.path.join(default_path, file_name), os.path.join(default_path, new_file_name))
                    feed_back = f"{new_file_name} added to #untagged"
                    tag_dict["#untagged"].append(new_file_name)
                    tags.append(new_file_name)
                    tab_tree.insert(new_file_name)
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
                    feed_back, tags, tag_dict, tab_tree = parse_command(command, tag_dict, tags, tab_tree)
                    entry.set_text("")
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
