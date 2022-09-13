import os
from flask import current_app
import logging
import datetime

from app.distance.mkad_polygon import MKAD_EXITS_COORDINATES

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from shapely.ops import nearest_points

from geopy.geocoders import Yandex


from app.distance import bp


logging.basicConfig(filename='flask_test.log', level=logging.INFO, format='%(asctime)s : %(message)s')


def check_adres(full_adres):
    """
    Функция проверяет корректность введенного адреса, который должен включать название города в московской области, и фактический адрес, разделенные запятой
    """
    if len(full_adres) != 0:
        lst = full_adres.split(',', maxsplit = 2)
        if len(lst) == 1:
            result = [False, 'Для более корректного геокодирования, введите как название города так и фактический адрес']
        else:
            return [True, 'Адрес корректный']
    else:
        result = [False, 'Введите корректный адрес']
    return result


def adres_to_coords(full_adres):
    """
    Функция возвращает кординаты введенного адреса
    """
    check, info = check_adres(full_adres)
    if check:
        geolocator = Yandex(api_key=os.environ.get('YANDEX_KEY'))
        query_adress = f'Россия Москва {full_adres}'
        location = geolocator.geocode(query=query_adress)
        if location: # если геокодер распознал адрес и вернул координаты
            latitude, longitude = location.latitude, location.longitude
            point = Point(latitude, longitude)
            # print(latitude, longitude)
            if latitude == 55.755819 and longitude == 37.617644: # координты Москвы
                return 'Адрес не распознан'
            else:
                return point
        else:
            return 'Адрес не распознан'
    else:
        return info



def calc_distance(full_adres):
    """
    Функция calc_distance - возвращет расстояние от точки point до ближайшей координаты полигона с точками съезда с МКАД
    MKAD_EXITS_COORDINATES - список координат со съездами с МКАД
    point - экземпляр класса Point библиотеки Shapely
    nearest_points - функция библиотеки Shapely, принимает два аргумента - объект Polygon и объект Point, возвращает ближайшую точку в полигоне к объекту Point
    distance - функция библиотеки geopy, возвращает расстояние между двумя координатами
    """
    polygon = Polygon(MKAD_EXITS_COORDINATES)
    point = adres_to_coords(full_adres)
    if type(point) == Point:
        if polygon.contains(point):
            return 'Точка находится в пределах МКАД'
        else:
            nearest_point = nearest_points(polygon, point)[0]
            np_x, np_y = nearest_point.x, nearest_point.y # координаты ближайщей точки полигона МКАД
            x, y = point.x, point.y # координаты введенного адреса
            from geopy import distance
            dist = distance.distance((np_x, np_y), (x, y)).km # расстояние между двумя координатами в км
            return f'Расстояние от {full_adres} до МКАД - {dist:.2f} км'
    elif type(point) == str:
        return point


def create_log_file(result):
    request_time = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    with open('test.log', 'a+') as f:
        f.write(f'Время запроса {request_time} ')
        f.write(result)
        f.write('\n')



@bp.route('/distance/<string:adres>')
def distance(adres):
    result = calc_distance(adres)
    current_app.logger.info(result)
    create_log_file(result)
    return result
