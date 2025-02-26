from fieldBox import FieldBox
import pygame, sys
from pygame.locals import *
import os
import shutil
import json

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

def get_files(root):
    for en in os.scandir(root):
        if en.name.lower() not in [".ds_store", "all_files.json"] and en.is_file(follow_symlinks=False):
            yield en.name

def initial_setup(root, cmds, vars_):
    tagged = os.path.join(root, "Documents/My Tagged Files")
    if os.path.exists(tagged) == False:
        os.mkdir(tagged)
        with open(os.path.join(tagged, 'all_files.json'), 'w') as file:
            json.dump({"#untagged": [], "#img": [], "#file": [], "#misc": []}, file, indent=4)
    with open(os.path.join(tagged, "all_files.json"), "r") as file:
        tag_dict = json.load(file)
    tags = [path for path in get_files(tagged)]
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

font_ = pygame.font.SysFont("Courier", 20)

def parse_command(command, tag_dict, tags, tab_tree, root_dir):
    command_list = command.strip().split(" > ")
    com = command_list[0].strip()
    if com == "!delete-file":
        command_list[1] = command_list[1].strip()
        if "#" in command_list[1]:
            return ["Invalid file name"], tags, tag_dict, tab_tree
        try:
            for t in tag_dict:
                if command_list[1] in tag_dict[t]:
                    tag_dict[t].remove(command_list[1])
            os.remove(os.path.join(root_dir, command_list[1]))
            tags.remove(command_list[1])
            tab_tree.remove(command_list[1])
            return [f"Removed {command_list[1]}"], tags, tag_dict, tab_tree
        except OSError:
            return ["File not found"], tags, tag_dict, tab_tree
        except:
            return ["Error deleting file"], tags, tag_dict, tab_tree 

    elif com == "!rename":
        command_list[1], command_list[2] = command_list[1].strip(), command_list[2].strip()
        if "#" in command_list[1] or "&" in command_list[1] or "#" in command_list[2] or "&" in command_list[2] or ">" in command_list[1] or ">" in command_list[2]:
            return ["Invalid file name"], tags, tag_dict, tab_tree
        try:
            for t in tag_dict:
                if command_list[1] in tag_dict[t]:
                    tag_dict[t][tag_dict[t].index(command_list[1])] = command_list[2]
            os.rename(os.path.join(root_dir, command_list[1]), os.path.join(root_dir, command_list[2]))
            tags[tags.index(command_list[1])] = command_list[2]
            tab_tree.remove(command_list[1])
            tab_tree.insert(command_list[2])
            return [f"Renamed {command_list[1]} to {command_list[2]}"], tags, tag_dict, tab_tree
        except OSError:
            return ["File not found"], tags, tag_dict, tab_tree
        except:
            return ["Error renaming file"], tags, tag_dict, tab_tree
    
    elif com == "!tag-add":
        command_list[1], command_list[2] = command_list[1].strip(), command_list[2].strip()
        if "#" in command_list[1]:
            return ["Invalid file name"], tags, tag_dict, tab_tree
        list_of_tags = command_list[2].split(" & ")

        for l in list_of_tags:
            if l[0] == "#" and l != "#untagged":
                l = l.strip()
                if l not in tag_dict:
                    tag_dict[l] = []
                    tab_tree.insert(l)
                tag_dict[l].append(command_list[1])
        return ["Tags added"], tags, tag_dict, tab_tree

    else:
        if "&" not in com and "#" not in com and ">" not in com:
            try:
                for t in tag_dict:
                    if com in tag_dict[t]:
                        os.system(f"cd '{root_dir}' && open '{com.strip()}'")
                        return [f"Opened {com.strip()}"], tags, tag_dict, tab_tree
                return ["Couldn't open file"], tags, tag_dict, tab_tree
            except:
                return ["Error opening file"], tags, tag_dict, tab_tree

        list_of_tags = com.strip().split(" & ")
        all_files = set(tag_dict[list_of_tags[0]])
        for ltf in list_of_tags:
            ltf = ltf.strip()
            all_files = all_files & set(tag_dict[ltf])
        return list(all_files), tags, tag_dict, tab_tree

feed_back = [""]
tokens = [] 
token = ""
vs = 0
ve = 15

while True:
    screen.fill((0,0,0))
    entry.render(screen)
    feed_surf = font_.render("\n".join(feed_back[vs:ve]), True, (255,255,255))
    screen.blit(feed_surf, (50, 80))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            with open(os.path.join(curr_path, "all_files.json"), "w") as file:
                json.dump(tag_dict, file, indent=4)
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
            if "#" in file_name or "&" in file_name or ">" in file_name:
                feed_back = ["Invalid file name"]
            else:
                if os.path.exists(os.path.join(curr_path, file_name)) == False:
                    new_file_name = file_name.replace(" ", "_")
                    shutil.move(file_path, curr_path)
                    os.rename(os.path.join(curr_path, file_name), os.path.join(curr_path, new_file_name))
                    feed_back = [f"{new_file_name} added to #untagged"]
                    tag_dict["#untagged"].append(new_file_name)
                    tags.append(new_file_name)
                    tab_tree.insert(new_file_name)
        elif event.type == pygame.KEYDOWN:
            if entry.is_active() == True and entry.is_hidden() == False:
                if (event.key == pygame.K_o) and (event.mod & pygame.KMOD_CTRL):
                    entry.set_inactive()
                elif event.key == pygame.K_BACKSPACE:
                    entry.remove_behind_cursor()
                    if token:
                        token = token[:-1]
                        if token == "":
                            token = tokens[-1] if tokens else ""
                            tokens = tokens[:-1]
                    suggestions = tab_tree.find_prefix(token)
                    suggestions.sort()
                    suggestions = suggestions[:10]
                    curr_sug = 0
                elif event.key == pygame.K_RETURN:
                    command = entry.get_text()
                    try:
                        feed_back, tags, tag_dict, tab_tree = parse_command(command, tag_dict, tags, tab_tree, curr_path)
                    except:
                        feed_back = ["Error"]
                    entry.set_text("")
                    entry.set_inactive()
                    token = ""
                    tokens = []
                elif event.key == pygame.K_LEFT:
                    entry.move_cursorx(-1)
                elif event.key == pygame.K_RIGHT:
                    entry.move_cursorx(1)
                
                elif event.key == pygame.K_TAB:
                    if suggestions:
                        token = suggestions[curr_sug]
                        entry.set_text("".join(tokens) + token)
                        curr_sug = (curr_sug+1)%len(suggestions)
                    else:
                        curr_sug = 0
                elif event.unicode:
                    entry.append_at_cursor(event.unicode)
                    if event.unicode == ">" or event.unicode == " " or event.unicode == "&":
                        tokens.append(token)
                        tokens.append(event.unicode)
                        suggestions = []
                        token = ""
                    else:
                        token += event.unicode
                        suggestions = tab_tree.find_prefix(token)
                        suggestions.sort()
                        suggestions = suggestions[:10]
                    curr_sug = 0
            elif event.key == pygame.K_UP:
                if vs > 0:
                    vs -= 1
                    ve -= 1
            elif event.key == pygame.K_DOWN:
                if ve < len(feed_back):
                    vs += 1
                    ve += 1
            elif (event.key == pygame.K_o) and (event.mod & pygame.KMOD_CTRL):
                entry.set_active()

    pygame.display.update()
    clock.tick(30)
