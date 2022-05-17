from .config import DRAW_DATA_PATH, draw_config
from asyncio.exceptions import TimeoutError
from .util import download_img
from bs4 import BeautifulSoup
from .util import remove_prohibited_str
from utils.http_utils import AsyncHttpx
from nonebot.log import logger
import asyncio
try:
    import ujson as json
except ModuleNotFoundError:
    import json


headers = {'User-Agent': '"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)"'}


async def update_requests_info(game_name: str):
    info_path = DRAW_DATA_PATH / f"{game_name}.json"
    try:
        with info_path.open('r', encoding='utf8') as f:
            data = json.load(f)
    except (ValueError, FileNotFoundError):
        data = {}
    try:
        if game_name in {'fgo', 'fgo_card'}:
            if game_name == 'fgo':
                url = 'http://fgo.vgtime.com/servant/ajax?card=&wd=&ids=&sort=12777&o=desc&pn='
            else:
                url = 'http://fgo.vgtime.com/equipment/ajax?wd=&ids=&sort=12958&o=desc&pn='
            for i in range(9999):
                response = await AsyncHttpx.get(f'{url}{i}', timeout=7)
                fgo_data = json.loads(response.text)
                if int(fgo_data['nums']) == 0:
                    break
                for x in fgo_data['data']:
                    x['name'] = remove_prohibited_str(x['name'])
                    key = x['name']
                    data = add_to_data(data, x, game_name)
                    await download_img(data[key]['头像'], game_name, key)
                    logger.info(f'{key} is update...')
        if game_name == 'onmyoji':
            url = 'https://yys.res.netease.com/pc/zt/20161108171335/js/app/all_shishen.json?v74='
            response = await AsyncHttpx.get(url, timeout=7)
            onmyoji_data = response.json()
            for x in onmyoji_data:
                x['name'] = remove_prohibited_str(x['name'])
                key = x['name']
                data = add_to_data(data, x, game_name)
                logger.info(f'{key} is update...')
        data = await _last_check(data, game_name)
    except TimeoutError:
        logger.warning(f'更新 {game_name} 超时...')
        return {}, 999
    except Exception as e:
        logger.warning(f'更新 {game_name} 失败 {type(e)}：{e}...')
        return {}, 999
    with info_path.open('w', encoding='utf8') as wf:
        json.dump(data, wf, ensure_ascii=False, indent=4)
    return data, 200


# 添加到字典
def add_to_data(data: dict, x: dict, game_name: str) -> dict:
    member_dict = {}
    if game_name == 'fgo':
        member_dict = {
            'id': x['id'],
            'card_id': x['charid'],
            '头像': x['icon'],
            '名称': x['name'],
            '职阶': x['classes'],
            '星级': x['star'],
            'hp': x['lvmax4hp'],
            'atk': x['lvmax4atk'],
            'card_quick': x['cardquick'],
            'card_arts': x['cardarts'],
            'card_buster': x['cardbuster'],
            '宝具': x['tprop'],
        }
    elif game_name == 'fgo_card':
        member_dict = {
            'id': x['id'],
            'card_id': x['equipid'],
            '头像': x['icon'],
            '名称': x['name'],
            '星级': x['star'],
            'hp': x['lvmax_hp'],
            'atk': x['lvmax_atk'],
            'skill_e': x['skill_e'].split('<br />')[: -1],
        }
    elif game_name == 'onmyoji':
        member_dict = {
            'id': x['id'],
            '名称': x['name'],
            '星级': x['level'],
        }
    data[member_dict['名称']] = member_dict
    return data


# 获取额外数据
async def _last_check(data: dict, game_name: str) -> dict:
    if game_name == 'fgo':
        semaphore = asyncio.Semaphore(draw_config.SEMAPHORE)
        url = 'http://fgo.vgtime.com/servant/'
        tasks = [
            asyncio.ensure_future(
                _async_update_fgo_extra_info(url, key, value['id'], semaphore)
            )
            for key, value in data.items()
        ]

        result = await asyncio.gather(*tasks)
        for x in result:
            for key in x.keys():
                data[key]['入手方式'] = x[key]['入手方式']
    elif game_name == 'onmyoji':
        url = 'https://yys.163.com/shishen/{}.html'
        for key, value_ in data.items():
            response = await AsyncHttpx.get(f'{url.format(data[key]["id"])}', timeout=7)
            soup = BeautifulSoup(response.text, 'lxml')
            data[key]['头像'] = "https:" + soup.find('div', {'class': 'pic_wrap'}).find('img')['src']
            await download_img(value_['头像'], game_name, key)
    return data


async def _async_update_fgo_extra_info(url: str, key: str, _id: str, semaphore):
    # 防止访问超时
    async with semaphore:
        for i in range(10):
            try:
                response = await AsyncHttpx.get(f'{url}{_id}', timeout=7)
                soup = BeautifulSoup(response.text, 'lxml')
                obtain = soup.find('table', {'class': 'uk-table uk-codex-table'}).find_all('td')[-1].text
                if obtain.find('限时活动免费获取 活动结束后无法获得') != -1:
                    obtain = ['活动获取']
                elif obtain.find('非限时UP无法获得') != -1:
                    obtain = ['限时召唤']
                elif obtain.find('&') == -1:
                    obtain = obtain.strip().split(' ')
                else:
                    obtain = obtain.strip().split('&')
                logger.info(f'Fgo获取额外信息 {key}....{obtain}')
                x = {key: {}}
                x[key]['入手方式'] = obtain
                return x
            except TimeoutError:
                logger.warning(f'访问{url}{_id} 第 {i}次 超时...已再次访问')
            except Exception as e:
                logger.warning(f'访问{url}{_id} 第 {i}次 发生错误：{e}...已再次访问')
    return {}






