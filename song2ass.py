from import_joy02 import*
import re, os

def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"
    new_title = re.sub(rstr, "_", title)
    return new_title

def furiNoK(orgText):
    lineText = re.sub('\\\\\(','｟',orgText.rstrip('$'))
    lineText = re.sub('\\\\\)','｠',lineText)
    lineText = re.sub('{?([^{}^\u3041-\u30FF]+)}?\(([\u3041-\u30FF]+)\)',r'{\\k0}\1|<\2{\\k0}',lineText)
    lineText = re.sub("｟",r"{\\k0}(",lineText)
    lineText = re.sub("｠",r"{\\k0})",lineText)
    return lineText

def assDiaLines(lines):
    markers = re.compile('[●〇◇◆]')
    def assTimeStamp(ms):
        cs = ms/10
        s,cs = divmod(cs,100)
        m,s = divmod(s,60)
        h,m = divmod(m,60)
        return str(int(h))+":"+str(int(m)).zfill(2)+":"+str(int(s)).zfill(2)+"."+str(int(cs)).zfill(2)

    line_number = 0
    temp_text = ''
    temp_start_time = None
    ass_text = ''
    for i,line in enumerate(lines):
        if line['has_next']:
            temp_text += "{\\-%s}" %(line['style']) + line['text'] + '{\\k'+ str(int((lines[i+1]['start_time']-lines[i]['end_time'])/10)) + '} '
            if temp_start_time:
                continue
            temp_start_time = assTimeStamp(line['start_time'])
            if line['effect']=='no_k' and not re.findall(markers,line['text']):
                temp_start_time = assTimeStamp(lines[i-1]['start_time'])
        else:
            if line['effect']=='no_k' and not re.findall(markers,line['text']):
                lines[i]['start_time'] = lines[i-1]['start_time']
                ass_style = 'noK'
            else:
                line_number += 1
                ass_style = 'K' + str(line_number%2+1)
            start_time = temp_start_time or assTimeStamp(line['start_time'])
            end_time = assTimeStamp(line['end_time'])
            text = temp_text + "{\\-%s}" %(line['style']) + line['text']
            temp_text = ''
            ass_text += 'Dialogue: 0,' + start_time + ',' + end_time + ',' + ass_style + ',,0,0,0,karaoke,' + text + '\n'
            temp_start_time = None
    return ass_text

def genAssHeader(luaStr):
    with open('sample.ass','r',encoding = 'utf-8') as assFile:
        assHeader = assFile.read()
        assHeader = re.sub(r'(prevline = {})',luaStr + r'; \1',assHeader)
    return assHeader

def toLuaColorTbl(styles_obj,style_names):

    def colorToBGR(color_tuple):
        bgrList = ['%02X' % i for i in color_tuple]
        return '&H' + "".join(reversed(bgrList)) + '&'

    luaStr = 'colors = {'
    for style_name in style_names:
        afterMainColour = colorToBGR(styles_obj[style_name].colors_on[0])
        afterBordColour = colorToBGR(styles_obj[style_name].colors_on[1])
        beforeMainColour = colorToBGR(styles_obj[style_name].colors[0])
        beforeBordColour = colorToBGR(styles_obj[style_name].colors[1])
        luaStr += r"{'%s','%s','%s','%s'}," %(beforeMainColour,beforeBordColour,afterMainColour,afterBordColour)
    luaStr += '}'
    return luaStr
    
def songToAss(song):

    lyric = song.compounds
    styles = song.styles
    artist = song.meta['artist'][None]
    title = song.meta['title'][None]
    styleNames = re.findall(r"'([A-Z])'",str(styles))
    luaStr = toLuaColorTbl(styles,styleNames)
    assHeader = genAssHeader(luaStr)
    lines = []
    for i in range(len(lyric)):
        style = str(lyric[i])[12:13]
        has_next = not (lyric[i][style].break_after or i==len(lyric)-1)
        if len(lyric[i].timing)>0: #lineInfo with syls
            effect = 'karaoke'
            lineText = ''
            timeInfo = lyric[i].timing
            sylsInfo = lyric[i][style].atoms #sylsInfo = atoms
            timeIndex = 0
            for j in range(len(sylsInfo)):
                if sylsInfo[j].particles: #particles is a list of syl (single syl with multiple kana) 
                    for k in range(sylsInfo[j].steps):
                        kTag = '{\\k' + str(round(timeInfo[timeIndex]*100)) + '}' #
                        timeIndex += 1
                        if k==0:
                            lineText += kTag + sylsInfo[j].text + '|<' + sylsInfo[j].particles[k].text
                        else:
                            lineText += kTag + '#|<' + sylsInfo[j].particles[k].text
                else:                     #single syl single kana
                    kTag = '{\\k' + str(round(timeInfo[timeIndex]*100)) + '}'
                    lineText += kTag + sylsInfo[j].text
                    timeIndex += 1
        else:    # type of a whole line or actor mark
            effect = 'no_k'
            lineText = lyric[i][style].source
            lineText = furiNoK(lineText)
        startTime = lyric[i].start
        endTime = lyric[i].end
        lines.append({'start_time':int(startTime*1000),
                        'end_time':int(endTime*1000),
                           'style':style,
                          'effect':effect,
                            'text':lineText.strip(),
                        'has_next':has_next})
    assText = assDiaLines(lines)
    return assHeader + assText,artist + ' - ' + title

def saveAssfile(assText,fileName):
    path = os.getcwd()
    assFolder = os.path.join(path,"ass")
    if not os.path.exists(assFolder):
        os.mkdir(assFolder)
    fileName = validateTitle(fileName)
    file = os.path.join(assFolder,str(fileName)+".ass")
    with open(file, "wb") as fd:
        fd.write(assText.encode("utf-8"))
    print("Successfully saved karaoke timed ass file: "+str(fileName)+".ass")

song = ''  #song object created by blitzloop-tools
saveAssfile(songToAss(song),'filename')
