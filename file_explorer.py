from fieldBox import FieldBox
import pygame, sys
from pygame.locals import *
import os
import shutil
import json

pygame.init()

screen = pygame.display.set_mode((1400, 750))
clock = pygame.time.Clock()
pygame.key.set_repeat(250, 25)
font_ = pygame.font.SysFont("Courier", 20)

class TextEditor:
    def __init__(self, x, y, width, height, font, text_color=(255, 255, 255), bg_color=(0, 0, 0)):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.text_color = text_color
        self.bg_color = bg_color
        self.lines = [""]
        self.line_num = 0
        self.line_index = 0
        self.indent = 0
        self.active = False
        self.file_path = None  # Track the file being edited
        
        # View properties
        self.view_start = 0
        self.view_end = 18  # Number of visible lines
        self.view_hs = 0  # Horizontal scroll start
        self.view_he = 110  # Horizontal scroll end
        
        # Selection/clipboard
        self.rel = 0  # For text selection
        self.clip = ""  # Clipboard

    def handle_event(self, event):
        if not self.active:
            return
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.indent > 0 and self.lines[self.line_num].strip() == "":
                    self.indent -= 1
                    self.line_index -= 4
                elif self.lines[self.line_num] == "":
                    if self.line_num != 0:
                        self.lines = self.lines[:self.line_num] + self.lines[self.line_num+1:]
                        self.line_num -= 1
                        if self.line_num < self.view_start:
                            self.view_start -= 1
                            self.view_end -= 1
                        self.line_index = len(self.lines[self.line_num])
                        if len(self.lines[self.line_num]) > 110:
                            self.view_he = len(self.lines[self.line_num]) - 110
                            self.view_hs = self.view_he - 110
                    elif self.line_num == 0:
                        self.line_index = 0
                else:
                    if self.line_index > 0:
                        self.lines[self.line_num] = self.lines[self.line_num][:self.line_index-1] + self.lines[self.line_num][self.line_index:]
                        self.line_index -= 1
                    elif self.line_index == 0 and self.line_num != 0:
                        self.lines[self.line_num-1] = self.lines[self.line_num-1] + self.lines[self.line_num]
                        self.line_index = len(self.lines[self.line_num-1]) - len(self.lines[self.line_num])
                        self.lines = self.lines[:self.line_num] + self.lines[self.line_num+1:]
                        self.line_num -= 1
                        if self.view_hs > 0:
                            self.view_hs = max(0, self.view_hs - 1)
                            self.view_he = self.view_hs + 110
                            
            elif event.key == pygame.K_DELETE:
                if self.line_index < len(self.lines[self.line_num]):
                    self.lines[self.line_num] = self.lines[self.line_num][:self.line_index] + self.lines[self.line_num][self.line_index+1:]
                elif self.line_num < len(self.lines) - 1:
                    # Join with next line when at end of current line
                    self.lines[self.line_num] = self.lines[self.line_num] + self.lines[self.line_num+1]
                    self.lines = self.lines[:self.line_num+1] + self.lines[self.line_num+2:]
                
            elif event.key == pygame.K_RETURN:
                if self.rel != 0:
                    self.rel = 0
                self.lines.insert(self.line_num+1, self.lines[self.line_num][self.line_index:])
                self.lines[self.line_num] = self.lines[self.line_num][:self.line_index]
                self.line_num += 1
                self.view_hs = 0
                self.view_he = 110
                if self.indent > 0:
                    self.lines[self.line_num] = "    " * self.indent + self.lines[self.line_num]
                    self.line_index = 4 * self.indent
                else:
                    self.line_index = 0
                if self.line_num > self.view_end - 1:
                    self.view_start += 1
                    self.view_end += 1
                
            elif event.key == pygame.K_LEFT:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                    self.line_index -= 1
                    self.rel -= 1
                    if self.line_index < 0:
                        self.line_index = 0
                        self.rel += 1
                else:
                    self.line_index -= 1
                    if self.line_index < 0:
                        # Move to end of previous line
                        if self.line_num > 0:
                            self.line_num -= 1
                            self.line_index = len(self.lines[self.line_num])
                            if self.line_num < self.view_start:
                                self.view_start -= 1
                                self.view_end -= 1
                        else:
                            self.line_index = 0
                    
                    if self.rel != 0:
                        self.rel = 0
                        
            elif event.key == pygame.K_RIGHT:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                    self.line_index += 1
                    self.rel += 1
                    if self.line_index > len(self.lines[self.line_num]):
                        self.line_index = len(self.lines[self.line_num])
                        self.rel -= 1
                else:
                    self.line_index += 1
                    if self.line_index > len(self.lines[self.line_num]):
                        # Move to beginning of next line
                        if self.line_num < len(self.lines) - 1:
                            self.line_num += 1
                            self.line_index = 0
                            if self.line_num >= self.view_end:
                                self.view_start += 1
                                self.view_end += 1
                        else:
                            self.line_index = len(self.lines[self.line_num])
                    
                    if self.rel != 0:
                        self.rel = 0
                        
            elif event.key == pygame.K_UP:
                if self.line_num > 0:
                    self.line_num -= 1
                    if self.line_num < self.view_start:
                        self.view_start -= 1
                        self.view_end -= 1
                    
                    if len(self.lines[self.line_num]) < self.line_index:
                        self.line_index = len(self.lines[self.line_num])
                
            elif event.key == pygame.K_DOWN:
                if self.line_num < len(self.lines) - 1:
                    self.line_num += 1
                    if self.line_num >= self.view_end:
                        self.view_start += 1
                        self.view_end += 1
                    
                    if len(self.lines[self.line_num]) < self.line_index:
                        self.line_index = len(self.lines[self.line_num])
                        
            elif event.key == pygame.K_TAB:
                self.lines[self.line_num] = self.lines[self.line_num][:self.line_index] + "    " + self.lines[self.line_num][self.line_index:]
                if self.lines[self.line_num].strip() == "":
                    self.indent += 1
                self.line_index += 4
                
                if self.line_index > 110:
                    diff = self.line_index - 110
                    self.view_hs += diff
                    self.view_he += diff
                
            elif (event.key == pygame.K_c) and (event.mod & pygame.KMOD_CTRL):
                if self.rel != 0:
                    if self.rel < 0:
                        self.clip = self.lines[self.line_num][self.line_index:self.line_index-self.rel+1]
                    elif self.rel > 0:
                        self.clip = self.lines[self.line_num][self.line_index-self.rel:self.line_index]
                    self.rel = 0
                else:
                    # Copy current line if no selection
                    self.clip = self.lines[self.line_num]
                
            elif (event.key == pygame.K_x) and (event.mod & pygame.KMOD_CTRL):
                if self.rel != 0:
                    if self.rel < 0:
                        self.clip = self.lines[self.line_num][self.line_index:self.line_index-self.rel+1]
                        self.lines[self.line_num] = self.lines[self.line_num][:self.line_index] + self.lines[self.line_num][self.line_index-self.rel+1:]
                    elif self.rel > 0:
                        self.clip = self.lines[self.line_num][self.line_index-self.rel:self.line_index]
                        self.lines[self.line_num] = self.lines[self.line_num][:self.line_index-self.rel] + self.lines[self.line_num][self.line_index:]
                    self.rel = 0
                else:
                    # Cut current line if no selection
                    self.clip = self.lines[self.line_num]
                    self.lines.pop(self.line_num)
                    if not self.lines:
                        self.lines = [""]
                    if self.line_num >= len(self.lines):
                        self.line_num = len(self.lines) - 1
                    self.line_index = min(self.line_index, len(self.lines[self.line_num]))
                
            elif (event.key == pygame.K_v) and (event.mod & pygame.KMOD_CTRL):
                if '\n' in self.clip:
                    # Handle multi-line paste
                    clip_lines = self.clip.split('\n')
                    # Insert first part on current line
                    self.lines[self.line_num] = self.lines[self.line_num][:self.line_index] + clip_lines[0]
                    # Insert remaining lines
                    for i, line in enumerate(clip_lines[1:], 1):
                        self.lines.insert(self.line_num + i, line)
                    self.line_num += len(clip_lines) - 1
                    self.line_index = len(clip_lines[-1])
                else:
                    # Simple paste
                    self.lines[self.line_num] = self.lines[self.line_num][:self.line_index] + self.clip + self.lines[self.line_num][self.line_index:]
                    self.line_index += len(self.clip)
                
            elif (event.key == pygame.K_a) and (event.mod & pygame.KMOD_CTRL):
                # Insert line above
                self.lines.insert(self.line_num, "")
                self.line_index = 0
                self.view_hs = 0
                self.view_he = 110
                
            elif (event.key == pygame.K_b) and (event.mod & pygame.KMOD_CTRL):
                # Insert line below
                self.lines.insert(self.line_num + 1, "")
                self.line_num += 1
                if self.line_num >= self.view_end:
                    self.view_start += 1
                    self.view_end += 1
                self.line_index = 0
                self.view_hs = 0
                self.view_he = 110
                
            elif (event.key == pygame.K_d) and (event.mod & pygame.KMOD_CTRL):
                # Delete current line
                if len(self.lines) > 1:
                    self.lines.pop(self.line_num)
                    if self.line_num >= len(self.lines):
                        self.line_num = len(self.lines) - 1
                else:
                    self.lines[0] = ""
                self.line_index = min(self.line_index, len(self.lines[self.line_num]))
                
            elif event.unicode and not (event.mod & pygame.KMOD_CTRL):
                self.lines[self.line_num] = self.lines[self.line_num][:self.line_index] + event.unicode + self.lines[self.line_num][self.line_index:]
                self.line_index += 1
                
                if self.line_index > 110:
                    self.view_hs += 1
                    self.view_he += 1

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_color, self.rect)
        
        # Calculate visible portion of text
        visible_lines = self.lines[self.view_start:self.view_end]
        
        # Draw lines
        line_height = self.font.get_height()
        for i, line in enumerate(visible_lines):
            visible_text = line[self.view_hs:self.view_he]
            text_surface = self.font.render(visible_text, True, self.text_color)
            screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5 + i * line_height))
        
        # Draw cursor only if active
        if self.active:
            cursor_x = self.rect.x + 5 + self.font.size(self.lines[self.line_num][self.view_hs:self.view_hs + self.line_index])[0]
            cursor_y = self.rect.y + 5 + (self.line_num - self.view_start) * line_height
            
            if 0 <= (self.line_num - self.view_start) < self.view_end - self.view_start:
                # Draw cursor
                pygame.draw.line(screen, self.text_color, 
                                 (cursor_x, cursor_y), 
                                 (cursor_x, cursor_y + line_height))
                
                # Draw selection if any
                if self.rel != 0:
                    sel_width = self.font.size('m')[0] * abs(self.rel)
                    if self.rel < 0:
                        sel_x = cursor_x
                    else:
                        sel_x = cursor_x - sel_width
                    
                    sel_rect = pygame.Rect(sel_x, cursor_y, sel_width, line_height)
                    sel_surface = pygame.Surface((sel_width, line_height))
                    sel_surface.set_alpha(100)
                    sel_surface.fill((100, 100, 255))
                    screen.blit(sel_surface, sel_rect)

    def save_file(self):
        if self.file_path:
            with open(self.file_path, 'w') as file:
                file.write('\n'.join(self.lines))
            return f"File saved: {self.file_path}"
        return "No file path specified."

    def load_file(self, file_path):
        self.file_path = file_path
        with open(file_path, 'r') as file:
            content = file.read()
            self.lines = content.split('\n')
            if not self.lines:
                self.lines = [""]
        self.line_num = 0
        self.line_index = 0
        self.view_start = 0
        self.view_end = min(18, len(self.lines))
        self.view_hs = 0
        self.view_he = 110
        return f"File loaded: {file_path}"

    def new_file(self):
        self.lines = [""]
        self.line_num = 0
        self.line_index = 0
        self.file_path = None
        self.view_start = 0
        self.view_end = 18
        self.view_hs = 0
        self.view_he = 110
        return "New file created."
        
    def get_text(self):
        return '\n'.join(self.lines)
        
    def set_active(self, active=True):
        self.active = active 


text_editor = TextEditor(10, 100, 1380, 600, font_, text_color=(255, 255, 255), bg_color=(0, 0, 0))
text_editor_active = False

entry = FieldBox(10, 50, entry_color=(255,255,255), text_color=(255,255,255), max_chars=115)

suggestions = []
curr_sug = 0
tag_dict = {}

cmds = ["!delete-file", "!tag-add", "!tag-remove", "!rename", "!tag-remove-all", "!tag-show", "!new-file", "!edit", "!save"]
vars_ = []

def get_files(root):
    for en in os.scandir(root):
        if en.name.lower() not in [".ds_store", "_#all_#files.json"] and en.is_file(follow_symlinks=False):
            yield en.name

def initial_setup(root, cmds, vars_):
    tagged = os.path.join(root, "Documents/My Tagged Files")
    if os.path.exists(tagged) == False:
        os.mkdir(tagged)
        with open(os.path.join(tagged, '_#all_#files.json'), 'w') as file:
            json.dump({"#all": [], "#img": [], "#file": [], "#misc": []}, file, indent=4)
    with open(os.path.join(tagged, "_#all_#files.json"), "r") as file:
        tag_dict = json.load(file)
    tags = [path for path in get_files(tagged)]
    tgc = tags.copy()
    tag_dict["#all"] = tgc
    tags.extend([t for t in tag_dict])
    tags.extend(cmds)
    tags.extend(vars_)
    curr_path = tagged
    return tags, curr_path, tag_dict

print("Initializing...")
tags, curr_path, tag_dict = initial_setup(os.path.expanduser("~"), cmds, vars_)

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


def parse_command(command, tag_dict, tags, tab_tree, root_dir):
    command_list = command.strip().split(" > ")
    com = command_list[0].strip()
    global text_editor_active
    if com == "!new-file":
        result = text_editor.new_file()
        text_editor.set_active(True)  # Activate the editor
        text_editor_active = True     # Set the global flag
        return [result], tags, tag_dict, tab_tree, (0, 255, 0)
    
    elif com == "!edit":
        if len(command_list) > 1:
            file_name = command_list[1].strip()
            if file_name in tags:
                file_path = os.path.join(root_dir, file_name)
                result = text_editor.load_file(file_path)
                text_editor.set_active(True)  # Activate the editor
                text_editor_active = True     # Set the global flag
                return [result], tags, tag_dict, tab_tree, (0, 255, 0)
            else:
                return ["File not found"], tags, tag_dict, tab_tree, (255, 0, 0)
        else:
            return ["Please specify a file to edit"], tags, tag_dict, tab_tree, (255, 0, 0)
    
    elif com == "!save":
        if text_editor.file_path:
            result = text_editor.save_file()
            text_editor.set_active(False)  # Deactivate the editor after saving
            text_editor_active = False     # Reset the global flag
            return [result], tags, tag_dict, tab_tree, (0, 255, 0)
        else:
            if len(command_list) > 1:
                file_name = command_list[1].strip()
                if "#" in file_name or "&" in file_name or ">" in file_name:
                    return ["Invalid file name"], tags, tag_dict, tab_tree, (255, 0, 0)
                file_path = os.path.join(root_dir, file_name)
                text_editor.file_path = file_path
                if file_name not in tag_dict["#all"]:
                    tag_dict["#all"].append(file_name)
                    tags.append(file_name)
                    tab_tree.insert(file_name)
                result = text_editor.save_file()
                text_editor.set_active(False)  # Deactivate the editor after saving
                text_editor_active = False     # Reset the global flag
                return [result], tags, tag_dict, tab_tree, (0, 255, 0)
            else:
                return ["Please specify a file name to save"], tags, tag_dict, tab_tree, (255, 0, 0)

    elif com == "!delete-file":
        if len(command_list) > 1:
            command_list[1] = command_list[1].strip()
            if "#" in command_list[1]:
                return ["Invalid file name"], tags, tag_dict, tab_tree, (255,0,0)
            try:
                for t in tag_dict:
                    if command_list[1] in tag_dict[t]:
                        tag_dict[t].remove(command_list[1])
                os.remove(os.path.join(root_dir, command_list[1]))
                tags.remove(command_list[1])
                tab_tree.remove(command_list[1])
                return [f"Removed {command_list[1]}"], tags, tag_dict, tab_tree, (0,255,0)
            except OSError:
                return ["File not found"], tags, tag_dict, tab_tree, (255,0,0)
            except:
                return ["Error deleting file"], tags, tag_dict, tab_tree, (255,0,0)
        else:
            return ["Please specify a file to edit"], tags, tag_dict, tab_tree, (255, 0, 0)

    elif com == "!rename":
        if len(command_list) > 2:
            command_list[1], command_list[2] = command_list[1].strip(), command_list[2].strip()
            if "#" in command_list[1] or "&" in command_list[1] or "#" in command_list[2] or "&" in command_list[2] or ">" in command_list[1] or ">" in command_list[2]:
                return ["Invalid file name"], tags, tag_dict, tab_tree, (255,0,0)
            try:
                for t in tag_dict:
                    if command_list[1] in tag_dict[t]:
                        tag_dict[t][tag_dict[t].index(command_list[1])] = command_list[2]
                os.rename(os.path.join(root_dir, command_list[1]), os.path.join(root_dir, command_list[2]))
                tags[tags.index(command_list[1])] = command_list[2]
                tab_tree.remove(command_list[1])
                tab_tree.insert(command_list[2])
                return [f"Renamed {command_list[1]} to {command_list[2]}"], tags, tag_dict, tab_tree, (0,255,0)
            except OSError:
                return ["File not found"], tags, tag_dict, tab_tree, (255,0,0)
            except:
                return ["Error renaming file"], tags, tag_dict, tab_tree, (255,0,0)
        else:
            return ["Invalid input"], tags, tag_dict, tab_tree, (255,0,0)

    elif com == "!tag-remove-all":
        command_list[1] = command_list[1].strip()
        if "#" in command_list[1] or command_list[1] not in tags:
            return ["Invalid file name"], tags, tag_dict, tab_tree, (255,0,0)
        
        rem_tag = []
        for l in tag_dict:
            if l != "#all":
                l = l.strip()
                tag_dict[l].remove(command_list[1])
                if tag_dict[l] == []:
                    rem_tag.append(l)
                    tab_tree.remove(l)
                    tags.remove(l)
        for r_ in rem_tag:
            del tag_dict[r_]
        return ["Tags removed"], tags, tag_dict, tab_tree, (0,255,0)

    elif com == "!tag-remove":
        command_list[1], command_list[2] = command_list[1].strip(), command_list[2].strip()
        if "#" in command_list[1] or command_list[1] not in tags:
            return ["Invalid file name"], tags, tag_dict, tab_tree, (255,0,0)
        list_of_tags = command_list[2].split(" & ")

        for l in list_of_tags:
            if l[0] == "#" and l != "#all":
                l = l.strip()
                if l in tag_dict:
                    tag_dict[l].remove(command_list[1])
                    if tag_dict[l] == []:
                        del tag_dict[l]
                        tab_tree.remove(l)
                        tags.remove(l)
        return ["Tags removed"], tags, tag_dict, tab_tree, (0,255,0)

    elif com == "!tag-add":
        command_list[1], command_list[2] = command_list[1].strip(), command_list[2].strip()
        if "#" in command_list[1] or command_list[1] not in tags:
            return ["Invalid file name"], tags, tag_dict, tab_tree, (255,0,0)
        list_of_tags = command_list[2].split(" & ")

        for l in list_of_tags:
            if l[0] == "#" and l != "#all":
                l = l.strip()
                if l not in tag_dict:
                    tag_dict[l] = []
                    tab_tree.insert(l)
                    tags.append(l)
                tag_dict[l].append(command_list[1])
        return ["Tags added"], tags, tag_dict, tab_tree, (0,255,0)

    elif com == "!tag-show":
        command_list[1] = command_list[1].strip()
        if "#" in command_list[1] or command_list[1] not in tags:
            return ["Invalid file name"], tags, tag_dict, tab_tree, (255,0,0)
        all_tags = []
        for t in tag_dict:
            if command_list[1] in tag_dict[t]:
                all_tags.append(t)
        return all_tags, tags, tag_dict, tab_tree, (255,255,0)

    elif com == "se":
        try:
            os.system(f"open https://google.com/search?q={command_list[1]}")
            return ["Google"], tags, tag_dict, tab_tree, (0,255,0)
        except:
            return ["Error"], tags, tag_dict, tab_tree, (255,0,0)

    else:
        if "&" not in com and "#" not in com and ">" not in com:
            try:
                for t in tag_dict:
                    if com in tag_dict[t]:
                        os.system(f"cd '{root_dir}' && open '{com.strip()}'")
                        return [f"Opened {com.strip()}"], tags, tag_dict, tab_tree, (0,255,0)
                return ["Couldn't open file"], tags, tag_dict, tab_tree, (255,0,0)
            except:
                return ["Error opening file"], tags, tag_dict, tab_tree, (255,0,0)

        list_of_tags = com.strip().split(" & ")
        all_files = set(tag_dict[list_of_tags[0]])
        for ltf in list_of_tags:
            ltf = ltf.strip()
            all_files = all_files & set(tag_dict[ltf])
        return list(all_files), tags, tag_dict, tab_tree, (255,255,0)

feed_back = [""]
tokens = [] 
token = ""
vs = 0
ve = 20
curr_selection = 0
stat_color = (0,0,0)

# Main game loop
while True:
    screen.fill((0,0,0))
    
    # Draw text editor when active
    if text_editor_active:
        text_editor.draw(screen)
    
    # Always draw entry field
    entry.render(screen)
    
    # Draw feedback messages only when text editor is not active
    if not text_editor_active:
        for f in range(len(feed_back[vs:ve])):
            feed_surf = font_.render(feed_back[vs:ve][f], True, (255,255,255))
            screen.blit(feed_surf, (10, 80+f*30))
        
        # Draw selection box for feedbacks
        if entry.is_active() == False:
            pygame.draw.rect(screen, stat_color, (5, 75+30*curr_selection, 1392, 30), 2, 3)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            with open(os.path.join(curr_path, "_#all_#files.json"), "w") as file:
                json.dump(tag_dict, file, indent=4)
            sys.exit(0)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Handle clicks based on active state
                if text_editor_active:
                    # Check if click is within text editor bounds
                    if text_editor.rect.collidepoint(event.pos):
                        # Editor already active, do nothing
                        pass
                    else:
                        # Click outside editor could deactivate it, but let's keep it active
                        # until explicitly saved (!save command)
                        pass
                else:
                    # Normal command mode behavior
                    if entry.get_rect().collidepoint(event.pos) and entry.is_active() == False:
                        entry.set_active()
                    else:
                        entry.set_inactive()
                        
        elif event.type == pygame.DROPFILE:
            file_path = event.file
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            if "#" in file_name or "&" in file_name or ">" in file_name:
                feed_back = ["Invalid file name"]
            else:
                if os.path.exists(os.path.join(curr_path, file_name)) == False:
                    new_file_name = file_name.replace(" ", "_")
                    shutil.move(file_path, curr_path)
                    os.rename(os.path.join(curr_path, file_name), os.path.join(curr_path, new_file_name))
                    feed_back = [f"{new_file_name} added to #all"]
                    tag_dict["#all"].append(new_file_name)
                    tags.append(new_file_name)
                    tab_tree.insert(new_file_name)
                    
        elif event.type == pygame.KEYDOWN:
            # Handle events differently based on editor state
            if text_editor_active:
                # Pass all keyboard events to the text editor when it's active
                text_editor.handle_event(event)
                
                # Add a way to exit the editor (e.g., Ctrl+S to save)
                if (event.key == pygame.K_s) and (event.mod & pygame.KMOD_CTRL):
                    # Quick save functionality
                    if text_editor.file_path:
                        text_editor.save_file()
                        text_editor.set_active(False)
                        text_editor_active = False
                        feed_back = [f"File saved: {text_editor.file_path}"]
                    else:
                        # If no file path, need to provide one via the command line
                        entry.set_active()
                        entry.set_text("!save > ")
                        text_editor.set_active(False)
                        text_editor_active = False
                
                # Can also add Escape to cancel editing without saving
                elif event.key == pygame.K_ESCAPE:
                    # Confirm if the user wants to exit without saving
                    text_editor.set_active(False)
                    text_editor_active = False
                    feed_back = ["Editing canceled. Changes not saved."]
                    
            else:
                # Handle normal command mode input
                if entry.is_active() == True and entry.is_hidden() == False:
                    if (event.key == pygame.K_o) and (event.mod & pygame.KMOD_CTRL):
                        entry.set_inactive()
                    elif event.key == pygame.K_BACKSPACE:
                        entry.remove_behind_cursor()
                        if token:
                            token = token[:-1]
                        else:
                            if tokens:
                                tokens.pop(-1)
                            token = tokens[-1] if tokens else ""
                            tokens = tokens[:-1] if len(tokens) > 1 else []
                            entry.set_text("".join(tokens) + token if tokens else token)
                        suggestions = tab_tree.find_prefix(token)
                        suggestions.sort()
                        curr_sug = 0
                    elif event.key == pygame.K_RETURN:
                        command = entry.get_text()
                        if command:
                            feed_back, tags, tag_dict, tab_tree, stat_color = parse_command(command, tag_dict, tags, tab_tree, curr_path)
                        else:
                            feed_back = [""]
                            stat_color = (0,0,0)
                        if feed_back == []:
                            stat_color = (0,0,0)
                        entry.set_inactive()
                    elif (event.key == pygame.K_d) and (event.mod & pygame.KMOD_CTRL):
                        entry.set_text("")
                        token = ""
                        tokens = []
                        curr_selection = 0
                    elif event.key == pygame.K_TAB:
                        if suggestions:
                            token = suggestions[curr_sug]
                            entry.set_text("".join(tokens) + token if len(tokens) > 1 else token)
                            curr_sug = (curr_sug+1)%len(suggestions)
                        else:
                            curr_sug = 0
                    elif event.unicode:
                        entry.append_at_cursor(event.unicode)
                        if event.unicode == " " and token:
                            if token:
                                tokens.append(token)
                            tokens.append(" & " if token[0] == "#" else " > ")
                            entry.set_text("".join(tokens))
                            suggestions = []
                            token = ""
                        else:
                            token += event.unicode
                            suggestions = tab_tree.find_prefix(token)
                            suggestions.sort()
                        curr_sug = 0
                elif event.key == pygame.K_RETURN:
                    if stat_color == (255,255,0):
                        if feed_back[curr_selection][0] != "#":
                            os.system(f"cd '{curr_path}' && open '{feed_back[curr_selection].strip()}'")
                elif event.key == pygame.K_UP:
                    if curr_selection > 0:
                        if vs > 0:
                            vs -= 1
                            ve -= 1
                        curr_selection -= 1
                elif event.key == pygame.K_DOWN:
                    if curr_selection < len(feed_back)-1:
                        if curr_selection > 20:
                            vs += 1
                            ve += 1
                        curr_selection += 1
                elif (event.key == pygame.K_o) and (event.mod & pygame.KMOD_CTRL):
                    entry.set_active()
                elif event.key == pygame.K_ESCAPE:
                    with open(os.path.join(curr_path, "_#all_#files.json"), "w") as file:
                        json.dump(tag_dict, file, indent=4)
                    sys.exit(0)

    pygame.display.update()
    clock.tick(30)
