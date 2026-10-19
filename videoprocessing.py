import re
import shutil
import subprocess
from pathlib import Path

# ===================== 配置区，按需修改 =====================
DRY_RUN = False  # True试运行仅打印，不修改删除；确认无误改为False
FFMPEG_CMD = "ffmpeg"  # ffmpeg不在PATH就写绝对路径 r"C:\ffmpeg\bin\ffmpeg.exe"
# ffmpeg：视频流复制，音频转AAC 256k
FFMPEG_ARGS = [
    "-i", "video.mp4",
    "-i", "audio.mp3",
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "256k",
    "-y"
]
LOG_FILENAME = ".videoInfo"
# 下面的AUDIOFILECODE列表是音频文件名末尾部分的代码，暂时停止收录更多这样的代码，而使用目前的按音视频文件大小比较来确定的方法。
AUDIOFILECODE = ["30280", "30216"]
RAW_EXT = ".m4s"
# ===========================================================

def sanitize_filename(name: str) -> str:
    """清理Windows文件名非法字符"""
    bad_chars = r'<>:"/\|?*'
    for c in bad_chars:
        name = name.replace(c, "_")
    return name.strip()

def parse_videoinfo(log_path: Path):
    """解析 .videoInfo，匹配 "title":"xxx" , "groupTitle":"xxx" """
    text = log_path.read_text(encoding="utf-8")
    match_video = re.search(r'"title":"([^"]+)"', text)
    match_proj = re.search(r'"groupTitle":"([^"]+)"', text)
    if not match_video or not match_proj:
        return None, None
    videoname = sanitize_filename(match_video.group(1))
    projname = sanitize_filename(match_proj.group(1))
    return videoname, projname

def process_m4sfile(file_path: Path):
    """
    m4sfile二进制裁剪规则
    删除1~9字节(1起始=0~8)
    保留 data[9:]，原地覆盖写入
    """
    with open(file_path, "rb") as f:
        data = f.read()
    new_data = data[9:]
    if not DRY_RUN:
        with open(file_path, "wb") as f:
            f.write(new_data)
    print(f"[处理m4s] {file_path.name} 头部字节裁剪完成")

def main():
    root_dir = Path(__file__).parent
    print(f"脚本根目录：{root_dir.resolve()}")
    print(f"DRY_RUN模式: {DRY_RUN}\n")

    # 遍历根目录下所有子文件夹作为项目
    for project_folder in root_dir.iterdir():
        if not project_folder.is_dir():
            continue

        # 固定日志文件名：项目文件夹/.videoInfo
        log_file = project_folder / LOG_FILENAME
        if not log_file.exists():
            print(f"跳过 {project_folder.name}: 找不到 .videoInfo 文件")
            continue

        videoname, projname = parse_videoinfo(log_file)
        if videoname is None or projname is None:
            print(f"跳过 {project_folder.name}: 解析.videoInfo获取videoname/project失败")
            continue

        print(f"\n===== 项目文件夹: {project_folder.name} =====")
        print(f"project={projname}, videoname={videoname}")

        # 查找m4sfile素材
        raw_list = list(project_folder.glob(f"*{RAW_EXT}"))
        if len(raw_list) != 2:
            print(f"跳过：m4sfile数量不为2，当前:{len(raw_list)}")
            continue

        '''
        这段是原先按音频文件末尾的数码区分音视频的，目前弃用
        audio_raw = None
        video_raw = None
        for rf in raw_list:
            if any(code in rf.name for code in AUDIOFILECODE):
                audio_raw = rf
            else:
                video_raw = rf
        '''
        # 按文件大小排序：小的是音频，大的是视频
        raw_sorted = sorted(raw_list, key=lambda p: p.stat().st_size)
        audio_raw = raw_sorted[0]   # 较小 = 音频
        video_raw = raw_sorted[1]   # 较大 = 视频

        if audio_raw is None or video_raw is None:
            print("跳过：无法区分音频/视频m4sfile")
            continue
        print(f"音频源: {audio_raw.name}, 视频源: {video_raw.name}")

        # 二进制裁剪处理m4sfile
        process_m4sfile(audio_raw)
        process_m4sfile(video_raw)

        # 重命名 m4sfile → audio.mp3 / video.mp4
        audio_mp3 = project_folder / "audio.mp3"
        video_mp4 = project_folder / "video.mp4"
        if not DRY_RUN:
            audio_raw.replace(audio_mp3)
            video_raw.replace(video_mp4)
        print(f"重命名：{audio_raw.name} -> audio.mp3 ; {video_raw.name} -> video.mp4")

        # 构建输出路径 output/project名/视频名.mp4
        output_proj_dir = root_dir / "output" / projname
        output_proj_dir.mkdir(parents=True, exist_ok=True)
        final_video = output_proj_dir / f"{videoname}.mp4"

        # ffmpeg命令
        ffmpeg_cmd = [FFMPEG_CMD] + FFMPEG_ARGS + [str(final_video)]
        print(f"执行ffmpeg: {' '.join(ffmpeg_cmd)}")
        ffmpeg_success = False
        if not DRY_RUN:
            proc = subprocess.run(ffmpeg_cmd, cwd=str(project_folder), capture_output=True, text=True)
            if proc.returncode != 0:
                print(f"FFMPEG混流失败！stderr:\n{proc.stderr}")
                continue
            ffmpeg_success = True
            print("✅ FFMPEG混流成功！")
        else:
            print("[试运行] FFMPEG模拟执行成功")
            ffmpeg_success = True

        # 混流成功：删除临时 audio.mp3 video.mp4，删除整个项目文件夹
        if ffmpeg_success and not DRY_RUN:
            audio_mp3.unlink(missing_ok=True)
            video_mp4.unlink(missing_ok=True)
            print("临时音视频文件已删除")

            shutil.rmtree(project_folder)
            print(f"🗑️ 原始项目文件夹 [{project_folder.name}] 已全部删除")

    print("\n==== 全部任务执行完毕 ====")

if __name__ == "__main__":
    main()
