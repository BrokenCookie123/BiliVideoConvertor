# BiliVideoConvertor
## Introduction
This is a small tool for convert video file that downloaded from Bilibili client to playable .mp4 file.
## Environment Require (Temporarily)
Because the tool has not been packed as a directly-use .exe, it needs some environments: **Python** and **FFmpeg**.
## Processing Mechanism
1. Read and extract the information (title, mainly) of video in its folder.
2. Find out two video and audio file. Though these two files share the same expandedname （“拓展名” 不会写QAQ） ".m4s", as is known to all, the video file always has bigger size than the audio one, thus the tool find out the bigger one as video, hence the other one is audio.
3. Delete 9 characters "000000000" (which are at the very begin of the original file) of these .m4s files, and save it, which make it a playable .mp3/.mp4 file.
4. Use FFmpeg to mix the video flow and audio flow. In case of .mp3 audio file can't be understood （“兼容” 不会写QAQ） by some players, the audio file is transformed to .aac audio file at the quality 255K.
5. Create an output folder to store the successfully converted videos, which has a structure as below (bold) :

(Bilibili savings catalog)
-bilibili
 |-load_log
 |-7355608(video folder that has not been converted)
 
 **|-output**
 
 **| |-Title**
 
 **| | |-Subtitle.mp4**
 
 **| |-人民万岁（4K）**
 
 **| | |-正片.mp4**
