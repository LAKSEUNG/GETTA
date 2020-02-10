# -*- coding: utf-8 -*-
from datetime import datetime
import sys
import os
import requests
import tqdm

import logging

import math

# For Proxies
proxies = {
  'http' : '47.210.39.111:13128',
  'https': '47.210.39.111:13128'
}

os_env_repo_home_dir = "D:/env_dir"
GIT_REQ_ADDRESS = ""

#os_env_repo_home_dir = os.environ["REPO_HOME_DIR"]
#GIT_REQ_ADDRESS = os.environ["GIT_REQ_ADDRESS"]

# repository folder     # global variables
REPOSITORY = os.path.join(os_env_repo_home_dir, "Git", "data", datetime.today().strftime("%Y%m%d"))
WORK_LOG = os.path.join(os_env_repo_home_dir, "Git", "log")


# 만약에 REPOSITORY폴더가 존재 하지 안는다면 생성 함
if not os.path.isdir(REPOSITORY):
    os.makedirs(REPOSITORY)

# 만약에 REPOSITORY폴더가 존재 하지 안는다면 생성 함
if not os.path.isdir(WORK_LOG):
    os.makedirs(WORK_LOG)

# Create the Logger Instance
logger = logging.getLogger(__name__)

# Create formatter for logger
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Make logger handler
stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(os.path.join(WORK_LOG, "git_work_"+datetime.today().strftime("%Y%m%d")+".log"))

stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

logger.setLevel(level=logging.INFO)


logger.info('REPOSITORY %s...' % REPOSITORY)

# I had to do this to setup max_retries in requests
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=2)
session.mount('https://', adapter)


def bar_custom(current, total, width=80):
    width=30
    avail_dots = width-2
    shaded_dots = int(math.floor(float(current) / total * avail_dots))
    percent_bar = '[' + '■'*shaded_dots + ' '*(avail_dots-shaded_dots) + ']'
    progress = "%d%% %s [%d / %d]" % (current / total * 100, percent_bar, current, total)
    return progress

def get_zip_file_name(line):
    logger.info('original request url is %s', line)
    spited_path = line.split('/')

    # 경로에서 Git의 USER와 REPO정보 추출 하기
    git_user = spited_path[3]
    git_repo = spited_path[4]

    logger.info('User String of Git is %s and Repo String of Git is %s', git_user, git_repo)

    #경로의 마지막 파일명을 추출
    spited_path.reverse()
    filename = spited_path[0]

    if not os.path.isdir(os.path.join(REPOSITORY, git_user, git_repo)):
        os.makedirs(os.path.join(REPOSITORY, git_user, git_repo))

    gen_filename = os.path.join(REPOSITORY, git_user, git_repo, filename)

    logger.info('generationed zip file name is %s', gen_filename)
    return gen_filename


def main_by_request(repository='', processes=0):
    appy_file_cnt = 0

    i = 0
    packages_downloaded = 0
    bytes_downloaded = 0

    pid = os.getpid()

    with open(GIT_REQ_ADDRESS, "r") as req_git_address_file:
        total = len(req_git_address_file.readlines())

    # GIT init File 을 읽어서 받을 요청 주소를 읽어 온다
    with open(GIT_REQ_ADDRESS, "r") as req_git_address_file:

        for line in req_git_address_file:

            try:
                i += 1
                zip_file_name = get_zip_file_name(line.strip())
                appy_file_cnt = appy_file_cnt + 1

                # 만약 이미 파일이 존재 하지 안는 다면 다운로드 실행
                if not os.path.isfile(os.path.join(REPOSITORY, zip_file_name)):

                    # For Proxies
                    #session.proxies.update(proxies)

                    resp = session.get(line.strip(), timeout=300, stream=True)
                    if not resp.status_code == requests.codes.ok:
                        resp.raise_for_status()

                    try:
                        file_size = int(resp.headers['content-length'])
                    except Exception as e:
                        file_size = 0

                    file_chunk = 1
                    chunk_size = 1024 * 3
                    num_bars = int(file_size / chunk_size)
                    progress = int(i / total * 100.0)

                    # save file
                    with open(os.path.join(REPOSITORY, zip_file_name), 'wb') as w:
                        for file_chunk in tqdm.tqdm(
                                resp.iter_content(chunk_size=chunk_size)
                                , total=num_bars
                                , unit='KB'
                                , desc=os.path.join(REPOSITORY, zip_file_name)
                                , leave=True  # progressbar stays
                                , position=1
                        ):
                            w.write(file_chunk)
                    # sum total bytes and count
                    bytes_downloaded += int(file_size)
                    packages_downloaded += 1

                    # verify with md5
                    # check = 'Ok' if hashlib.md5(resp.content).hexdigest() == md5_digest else 'md5 failed'
                    check = 'Ok'
                    logger.info('Downloaded: %-50s %s pid:%s %s%% [%s/%s]' % (os.path.join(REPOSITORY, zip_file_name), check, pid, progress, i, total))
                else:
                    logger.warning('[duplicate warning] Occurred the file duplicate error %s...' % os.path.join(REPOSITORY, zip_file_name))
                    # 파일이 중복 되는 경우 다운을 받지 않고 워닝 로그만 남긴다, 향후 변경 될수 있음.
            except Exception as ex:
                logger.error('Failed    : %s. %s' % (line, ex))

    logger.info(" ===> Complete download files from git hub, File Count: %i  !!!", appy_file_cnt)

if __name__ == '__main__':
    GIT_REQ_ADDRESS = sys.argv[1]
    logger.info('starting Git downloader ... requests file name is %s' % GIT_REQ_ADDRESS)
    main_by_request()
