import pygame, sys
from pygame.locals import *

def run_text_editor(initial_text=""):
    """
    Run a Pygame-based text editor.
    
    Args:
        initial_text (str, optional): Initial text to populate the editor with. Defaults to empty string.
    
    Returns:
        str: The filename that was saved, or None if no file was saved.
    """
    pygame.init()
    pygame.key.set_repeat(250, 25)

    clock = pygame.time.Clock()
    filename = None
    saved = False

    screen = pygame.display.set_mode((1400, 750))
    pygame.display.set_caption("Text Editor")
    cursorx = 48
    cursory = 25
    font = pygame.font.SysFont("Courier", 20)
    
    # Initialize lines - split initial text by newlines if provided
    if initial_text:
        lines = initial_text.strip().split('\n')
        if not lines:
            lines = [""]
    else:
        lines = [""]
    
    line_num = 0
    line_index = 0
    indent = 0
    clip = ""
    rel = 0
    clips = []

    view_start = 0
    view_end = 18

    view_hs = 0
    view_he = 110

    # Add save functionality
    def save_file():
        nonlocal filename, saved
        if not filename:
            # We're using a simple input mechanism since we can't use tkinter dialogs
            # from within pygame easily
            input_text = ""
            input_active = True
            while input_active:
                screen.fill((0, 0, 0))
                prompt_surf = font.render("Enter filename to save: " + input_text, True, (255, 255, 255))
                screen.blit(prompt_surf, (48, 25))
                pygame.display.flip()
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return None
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            input_active = False
                            filename = input_text
                        elif event.key == pygame.K_BACKSPACE:
                            input_text = input_text[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            return None
                        elif event.unicode:
                            input_text += event.unicode
                            
                clock.tick(20)
                
        if filename:
            with open(filename, 'w') as f:
                f.write('\n'.join(lines))
            saved = True
            return filename
        return None

    while True:
        clock.tick(20)
        screen.fill((0, 0, 0))
        if rel == 0:
            pygame.draw.rect(screen, (255, 255, 255), [cursorx, cursory, 12, 20], 2)
        
        if rel < 0:
            pygame.draw.rect(screen, (128, 128, 128), [cursorx+12, cursory, 12*(-rel), 20], 2)
        elif rel > 0:
            pygame.draw.rect(screen, (128, 128, 128), [cursorx-12*rel, cursory, 12*rel, 20], 2)

        in_view = lines[view_start:view_end]

        for i in range(len(in_view)):
            txt_surf = font.render(in_view[i][view_hs:view_he], True, (255, 255, 255))
            screen.blit(txt_surf, (48, 25+i*25))
        
        # Show filename or status in the window title
        if filename:
            status = f"Text Editor - {filename}"
            if not saved:
                status += " *"
            pygame.display.set_caption(status)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            if event.type == pygame.KEYDOWN:
                saved = False  # Any keypress except for save commands will mark as unsaved
                
                if event.key == pygame.K_BACKSPACE:
                    if indent > 0 and lines[line_num].strip() == "":
                        indent -= 1
                        cursorx -= 12*4
                        line_index -= 4
                    elif lines[line_num] == "":
                        if line_num != 0:
                            lines = lines[:line_num] + lines[line_num+1:]
                            line_num -= 1
                            cursory -= 25
                            if line_num < view_start: 
                                view_start -= 1
                                view_end -= 1
                                cursory = 25
                            line_index = len(lines[line_num])
                            if len(lines[line_num]) > 110:
                                 view_he = len(lines[line_num]) - 110
                                 view_hs = view_he - 110
                            cursorx = 48 + len(lines[line_num][view_hs:view_he])*12
                        elif line_num == 0:
                            if cursorx < 48:
                                cursorx = 48
                            line_index = 0
                        if cursory < 25:
                            cursory = 25
                    else:
                        lines[line_num] = lines[line_num][:line_index-1] + lines[line_num][line_index:] if line_index != 0 else lines[line_num]
                        if line_index == 0 and line_num!=0:
                            lines[line_num-1] = lines[line_num-1]+lines[line_num]
                            cursorx = 48 + len(lines[line_num-1])*12 - len(lines[line_num])*12
                            cursory -= 25
                            line_index = len(lines[line_num-1]) - len(lines[line_num])
                            lines = lines[:line_num] + lines[line_num+1:]
                            line_num -= 1
                        else:
                            cursorx -= 12
                            line_index -= 1
                            if cursorx < 48:
                                cursorx = 48
                                view_hs -= 1
                                if view_hs < 0: view_hs = 0
                                view_he -= 1
                                if view_he < 110: view_he = 90
                            if line_index < 0: line_index = 0

                elif event.key == pygame.K_RETURN:
                    if rel != 0: rel = 0
                    cursorx = 48
                    cursory += 25
                    lines.insert(line_num+1, lines[line_num][line_index:])
                    lines[line_num] = lines[line_num][:line_index]
                    line_num += 1
                    view_hs = 0
                    view_he = 110
                    if indent > 0:
                        lines[line_num] = "    "*indent + lines[line_num]
                        line_index = 4*indent
                        cursorx += 12*4*indent
                    else:
                        line_index = 0
                    if line_num > view_end-1:
                        view_start += 1
                        view_end += 1            
                    if cursory > 450:
                        cursory = 450

                elif event.key == pygame.K_LEFT:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                        cursorx -= 12
                        line_index -= 1
                        rel -= 1
                        if cursorx < 36:
                            cursorx = 36
                            line_index = -1
                            rel += 1
                    else:
                        cursorx -= 12
                        line_index -= 1
                        if cursorx < 48 and rel==0:
                            cursorx = 48
                            view_hs -= 1
                            if view_hs < 0: view_hs = 0
                            view_he -= 1
                            if view_he < 110: view_he = 90

                        if rel != 0:
                            rel -= 1
                            if cursorx < 36:
                                cursorx = 36
                                line_index = -1
                                rel += 1
                        if line_index < 0: line_index = 0 
                
                elif event.key == pygame.K_RIGHT:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                        cursorx += 12
                        line_index += 1
                        rel += 1
                        if cursorx > 48+len(lines[line_num])*12:
                            cursorx = 48+len(lines[line_num])*12
                            line_index = len(lines[line_num])
                            rel -= 1
                    else:
                        cursorx += 12
                        line_index += 1
                        if cursorx > 48+110*12:
                            cursorx = 48+110*12
                            view_hs += 1
                            if line_index > len(lines[line_num]):
                                line_index = len(lines[line_num])
                                view_hs -= 1
                            else:
                                view_he += 1
                            
                        if rel != 0:
                            rel += 1
                        if cursorx > 48+len(lines[line_num][view_hs:view_he])*12:
                            cursorx = 48+len(lines[line_num][view_hs:view_he])*12
                            line_index = len(lines[line_num])
                            if rel != 0:
                                rel -= 1            

                elif rel != 0 and event.key == pygame.K_x:
                    if rel < 0:
                        clip = lines[line_num][line_index:line_index-rel+1]
                        lines[line_num] = lines[line_num][:line_index] + lines[line_num][line_index-rel+1:]
                    elif rel > 0:
                        clip = lines[line_num][line_index-rel:line_index]
                        lines[line_num] = lines[line_num][:line_index-rel] +lines[line_num][line_index:]
                    rel = 0
                    if cursorx < 48:
                        cursorx = 48
                        line_index = 0
                    if cursorx > 48+len(lines[line_num])*12:
                        cursorx = 48+len(lines[line_num])*12
                        line_index = len(lines[line_num])
                
                elif rel != 0 and event.key == pygame.K_c:
                    if rel < 0:
                        clip = lines[line_num][line_index:line_index-rel+1]
                    elif rel > 0:
                        clip = lines[line_num][line_index-rel:line_index]
                    rel = 0
                    if cursorx < 48:
                        cursorx = 48
                        line_index = 0
                    if cursorx > 48+len(lines[line_num])*12:
                        cursorx = 48+len(lines[line_num])*12
                        line_index = len(lines[line_num])

                elif event.key == pygame.K_UP:
                    cursory -= 25
                    line_num -= 1
                    if line_num < 0:
                        line_num = 0
                    if cursory < 25:
                        cursory = 25
                    if line_num == view_start-1:
                        view_start -= 1
                        view_end -= 1
                    if len(lines[line_num]) < line_index:
                        prev_li = line_index
                        line_index = len(lines[line_num])
                        viewf = (len(lines[line_num+1])-len(lines[line_num]))
                        if viewf >= 110 and prev_li-line_index >= 90:
                            view_he -= viewf
                            if view_he < 110:
                                view_hs = 0
                                view_he = 110
                            else:
                                view_hs = view_he - 110
                        cursorx = 48+len(lines[line_num][view_hs:view_he])*12

                elif event.key == pygame.K_DOWN:
                    cursory += 25
                    line_num += 1
                    if line_num > len(lines)-1:
                        line_num = len(lines)-1
                        cursory -= 25
                    if cursory > 450:
                        cursory = 450
                    if line_num == view_end:
                        view_start += 1
                        view_end += 1
                    if len(lines[line_num]) < line_index:
                        prev_li = line_index
                        line_index = len(lines[line_num])
                        viewf = (len(lines[line_num-1])-len(lines[line_num]))
                        if viewf >= 110 and prev_li-line_index >= 90:
                            view_he -= viewf
                            if view_he < 110:
                                view_hs = 0
                                view_he = 110
                            else:
                                view_hs = view_he - 110
                        cursorx = 48+len(lines[line_num][view_hs:view_he])*12
                
                elif event.key == pygame.K_TAB:
                    lines[line_num] = lines[line_num][:line_index] + "    " + lines[line_num][line_index:]
                    if lines[line_num].strip() == "":
                        indent += 1
                    line_index += 4
                    cursorx += 12*4
                    if cursorx > 48+110*12:
                        diff = int((cursorx - (48+110*12))/12)
                        cursorx = 48+110*12
                        view_hs += diff
                        view_he += diff
                
                elif event.key == pygame.K_ESCAPE:
                    return None
                
                # Save functionality with Ctrl+S
                elif (event.key == pygame.K_s) and (event.mod & pygame.KMOD_CTRL):
                    saved = True
                    saved_file = save_file()
                    if saved_file:
                        filename = saved_file
                
                elif (event.key == pygame.K_v) and (event.mod & pygame.KMOD_CTRL):            
                    lines[line_num] = lines[line_num][:line_index] + clip + lines[line_num][line_index:]
                    line_index += len(clip)
                    cursorx += 12*len(clip)
                    if cursorx > 48+110*12:
                        diff = int((cursorx - (48+110*12))/12)
                        cursorx = 48+110*12
                        view_hs += diff
                        view_he += diff

                elif (event.key == pygame.K_a) and (event.mod & pygame.KMOD_CTRL):
                    cursorx = 48
                    lines.insert(line_num, "")
                    line_index = 0
                    view_hs = 0
                    view_he = 110

                elif (event.key == pygame.K_b) and (event.mod & pygame.KMOD_CTRL):
                    cursorx = 48
                    cursory += 25
                    if cursory > 450:
                        cursory = 450
                    lines.insert(line_num+1, "") 
                    line_num += 1
                    if line_num == view_end:
                        view_start += 1
                        view_end += 1
                    line_index = 0
                    view_hs = 0
                    view_he = 110

                elif (event.key == pygame.K_d) and (event.mod & pygame.KMOD_CTRL):
                    if line_num != 0:
                        lines = lines[:line_num] + lines[line_num+1:]
                        if line_num == len(lines):
                            line_num -= 1
                            if line_num == view_start-1:
                                view_start -= 1
                                view_end -= 1
                            cursory -= 25
                            if cursory < 25:
                                cursory = 25
                    else:
                        if len(lines) > 1:
                            lines = lines[1:]
                        else:
                            lines[line_num] = ""
                    cursorx = 48
                    line_index = 0
                    view_hs = 0
                    view_he = 110

                elif event.unicode:
                    lines[line_num] = lines[line_num][:line_index] + event.unicode + lines[line_num][line_index:]
                    line_index += 1
                    cursorx += 12
                    if cursorx > 48+110*12:
                        cursorx = 48+110*12
                        view_hs += 1
                        view_he += 1
                            
        pygame.display.flip()
