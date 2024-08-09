from selenium import webdriver
import json
import pymysql
from datetime import datetime
from selenium.common.exceptions import WebDriverException
from urllib.parse import parse_qs, urlparse
from source import host, port, user, password, database, oper_table, vtb_table, alfa_table, tbank_table, proxy_table, referal_link_tbank, referal_link_365days, referal_link_travel

            ### для работы необходим хром драйвер!
### Логизация через SQL базу
while True:
    try:
        oper = input("Фамилия И. О. оператора: ")
        connection = pymysql.connect(
            host = host,
            port= port,
            user = user,
            password = password,
            database = database,
            charset = "utf8mb4",
            cursorclass = pymysql.cursors.DictCursor)
    except:
        print("Ошибка подключения SQL, перезагрузите или зайдите позже.")
    
    with connection.cursor() as cursor:
        select_link = f"SELECT link FROM `{oper_table}` WHERE oper = '{oper}';"
        cursor.execute(select_link)
        op_link = cursor.fetchone()
        try:
            op_link_done = op_link['link']
        except:
            pass
    
    with connection.cursor() as cursor:
        select_all_rows = f"SELECT * FROM `{oper_table}` WHERE oper = '{oper}';"
        cursor.execute(select_all_rows)
        rows = cursor.fetchall()
        found = False
        for row in rows:
            if row["oper"] == oper:
                op_id = row["id"]
                found = True
                break
        if found:
            break

### Подключение прокси из SQL таблицы
while True:
    proxy = str(input("Использовать прокси - 1, нет - 2: "))
    if proxy == "1":
        try:  
            with connection.cursor() as cursor:
                select_all_rows = f"SELECT city FROM `{oper_table}` WHERE oper = '{oper}';"
                cursor.execute(select_all_rows)
                rows = cursor.fetchall()
                for row in rows:
                    town = row['city']
            with connection.cursor() as cursor:
                select_all_rows = f"SELECT * FROM `{proxy_table}` WHERE city = '{town}' ORDER BY RAND() LIMIT 1;"
                cursor.execute(select_all_rows)
                rows = cursor.fetchall()
                for row in rows:
                    proxy_host = row['host']
                    proxy_port = row['port']
                    if proxy_host == "" or proxy_host == None:
                        proxy_host = "err"
                        proxy_port = "err"
                        print("Прокси отсутствует")
                    else:
                        print("Прокси подключен")
            break
        except:
            proxy_host = "err"
            proxy_port = "err"
            print("Can't find proxy_1")
    elif proxy == "2":
        proxy_host = "err"
        proxy_port = "err"
        break
    else:
        continue

### Основной цикл работы
while True:
    # Выбор карты
    while True:
        choise = str(input('Анкета "T-Bank" - 1, Анкета "VTB" - 2, Анкета "365 Дней" - 3, "Тревел" - 4, Смена прокси - 5: '))
        if choise == "1":
            url_start = f"{referal_link_tbank}={op_id}"
            print('Заявка на карту "T-Bank"')
            break
        elif choise == "2":
            url_start = op_link_done # для каждого оператора ссылка уникальна в рамках ВТБ
            print('Заявка на карту "VTB"')
            break
        elif choise == "3":
            url_start = f"{referal_link_365days}={op_id}"
            print('Заявка на карту "365 Дней без процентов"')
            break
        elif choise == "4":
            url_start = f"{referal_link_travel}={op_id}"
            print('Заявка на карту "Тревел"')
            break
        elif choise == "5":
            print("Смена прокси...")
            try:
                with connection.cursor() as cursor:
                    select_all_rows = f"SELECT * FROM `{proxy_table}` WHERE city = '{town}' ORDER BY RAND() LIMIT 1;"
                    cursor.execute(select_all_rows)
                    rows = cursor.fetchall()
                    for row in rows:
                        proxy_host = row['host']
                        proxy_port = row['port']
                        if proxy_host == "" or proxy_host == None:
                            print("Прокси пуст")
                        else:
                            print("Прокси изменен")
                            print(proxy_host, proxy_port)
            except:
                proxy_host = "err"
                proxy_port = "err"
                print("Ошибка прокси")
            continue
        else:
            continue
    
    # Старт работы в браузере на выбранном сайте
    try:
        chrome_options = webdriver.ChromeOptions()
        # Подключение прокси
        if proxy_host != proxy_port:
            chrome_options.add_argument(f'--proxy-server={proxy_host}:{proxy_port}')
        else:
            pass
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        # 2 строки выше вариант отключения капчи в заявках
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.set_capability(
            "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
        )
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()
        
        # Анкета "T-Bank"
        if choise == '1':
            driver.get(url_start)

            # поисковик ключевых слов
            def parse_json(json_string, search_key):
                data = json.loads(json_string)
                for key, value in data.items():
                    if key == search_key:
                        return value
                    elif isinstance(value, dict):
                        result = parse_json(json.dumps(value), search_key)
                        if result is not None:
                            return result
                return None

            def save_cookie():
                cookies_l = driver.get_cookies()
                my_dict_l = {cookie_l['name']: cookie_l['value'] for cookie_l in cookies_l}
                cookie_json_l = json.dumps(my_dict_l)

                with connection.cursor() as cursor:
                    update_query = f"UPDATE `{tbank_table}` SET\
                        cookie_last = '{cookie_json_l}'\
                        WHERE id = {oper_maxid_done};"
                    cursor.execute(update_query)
                    connection.commit()

            def save_cookie_1():
                cookies = driver.get_cookies()
                my_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                cookie_json = json.dumps(my_dict)

                with connection.cursor() as cursor:
                    update_query = f"UPDATE `{tbank_table}` SET\
                        cookie = '{cookie_json}'\
                        WHERE id = {oper_maxid_done};"
                    cursor.execute(update_query)
                    connection.commit()

            now = datetime.now()
            now_formt = now.strftime("%Y-%m-%d %H:%M:%S")
            with connection.cursor() as cursor:
                insert_query = f"INSERT INTO `{tbank_table}` (data_time, oper) VALUES ('{now_formt}', '{oper}');" 
                cursor.execute(insert_query)
                connection.commit()

            with connection.cursor() as cursor:
                select_qiery = f"SELECT MAX(id) FROM `{tbank_table}` WHERE oper = '{oper}';"
                cursor.execute(select_qiery)
                connection.commit()
                oper_maxid = cursor.fetchone()
                oper_maxid_done = oper_maxid['MAX(id)']

                try:
                    save_cookie_1()
                except:
                    pass
                while True:
                    try:
                        log_entries = driver.get_log("performance")
                        for entry in log_entries:
                            message = entry["message"]
                            if "https://www.tbank.ru/api/common/v1/add_application?origin=web%2Cib5%2Cplatform&sessionid=" in message:
                                try:
                                    # print("@@@@@@@")
                                    # message_j = json.loads(message)
                                    # app_info = message_j["message"]["params"]["request"]["postData"]
                                    trash = ['","', '"},"', '"","']
                                    search_key = ['fio', 'desired_credit_limit', 'phone_mobile', 'product_name', 'tid', 'wuid', 'step_id', 'step_id_max', 'income_individual', 'work_position_text', 'dadata_management_post', 'work_name', 'dadata_inn', 'dadata_address_data_source', 'dadata_address_unrestricted_value', 'dadata_address_value', 'addresstype_home_area', 'addresstype_home_city', 'addresstype_home_place', 'timeOnStep2', 'timeOnStep3', 'timeOnStep4', 'id', 'sessionid', 'birthdate', 'id_division_code', 'place_of_birth', 'passport_date_given', 'passport_who_given', 'hittoken', 'passport_number', 'passport_series', 'addresstype_registered_area', 'addresstype_registered_city', 'addresstype_registered_place', 'addresstype_registered_building', 'addresstype_registered_street', 'addresstype_registered_corpus', 'addresstype_registered_stroenie', 'addresstype_registered_flat', 'employment_type', 'dadata_management_name', 'dadata_name_short_with_opf', 'appLogScoringResult']
                                    parsed_url = urlparse(message)
                                    query_params = parse_qs(parsed_url.query)
                                    data_info = [query_params.get(key, [''])[0] for key in search_key]
                                    # print(app_info)
                                    # for i, item in enumerate(data_info):
                                    #     if item:
                                    #         print(f"Index {i}: {item}")
                                    # помогает проверить какими данными меняемся с банком
                                    # частично данные сейвились с мусором, костыль который помогает этого избежать (trash)
                                    with connection.cursor() as cursor:
                                        for i, item in enumerate(data_info):
                                            if item:
                                                for t in trash:
                                                    if t in item:
                                                        item = item.split(t)[0]
                                                        break
                                                update_query = f"UPDATE `{tbank_table}` SET `Index {i}` = '{item}' WHERE id = {oper_maxid_done};"
                                                cursor.execute(update_query)
                                        connection.commit()
                                except:
                                    pass
                        if len(driver.window_handles) == 0:
                            pass
                        else:
                            try:
                                save_cookie()
                            except:
                                pass
                    except WebDriverException:
                        break
        
        # Анкета "VTB"
        elif choise == '2':
            driver.get(url_start)

            # поисковик ключевых слов
            def parse_json(json_string, search_key):
                data = json.loads(json_string)
                for key, value in data.items():
                    if key == search_key:
                        return value
                    elif isinstance(value, dict):
                        result = parse_json(json.dumps(value), search_key)
                        if result is not None:
                            return result
                return None

            def save_cookie():
                cookies_l = driver.get_cookies()
                my_dict_l = {cookie_l['name']: cookie_l['value'] for cookie_l in cookies_l}
                cookie_json_l = json.dumps(my_dict_l)

                with connection.cursor() as cursor:
                    update_query = f"UPDATE `{vtb_table}` SET\
                        cookie_last = '{cookie_json_l}'\
                        WHERE id = {oper_maxid_done};"
                    cursor.execute(update_query)
                    connection.commit()

            def save_cookie_1():
                cookies = driver.get_cookies()
                my_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                cookie_json = json.dumps(my_dict)

                with connection.cursor() as cursor:
                    update_query = f"UPDATE `{vtb_table}` SET\
                        cookie = '{cookie_json}'\
                        WHERE id = {oper_maxid_done};"
                    cursor.execute(update_query)
                    connection.commit()

            def step1():
                if phone_s is None:
                    pass
                else:
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{vtb_table}` SET tel = '{phone_s}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()

                with connection.cursor() as cursor:
                    update_query = f"UPDATE `{vtb_table}` SET \
                        fio = '{lastname_s + ' ' + firstname_s + ' ' + middlename_s}',\
                        birthDate = '{birthDate_s}'\
                        WHERE id = {oper_maxid_done};"
                    cursor.execute(update_query)
                    connection.commit()

            def step2():
                if series_s is None:
                    pass
                else:
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{vtb_table}` SET \
                            gender = '{gender_s}',\
                            birthPlace = '{birthPlace_s}',\
                            email = '{email_s}',\
                            series = '{series_s}',\
                            number = '{number_s}',\
                            issueDate = '{issueDate_s}',\
                            issueName = '{issueName_s}',\
                            issueCode = '{issueCode_s}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()

            def step3():
                if typeRef_s is None:
                    pass
                else:
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{vtb_table}` SET\
                            fullAddress = '{fullAddress_s}',\
                            educationInfo = '{educationInfo_s}',\
                            maritalStatusRef = '{maritalStatusRef_s}',\
                            underageChildrenNumber = '{underageChildrenNumber_s}',\
                            typeRef = '{typeRef_s}',\
                            amount = '{amount_s}',\
                            employerTin = '{employerTin_s}',\
                            employerName = '{employerName_s}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()

            def step4():
                if deliveryDate_s is None:
                    pass
                else:
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{vtb_table}` SET\
                            deliveryAddress = '{fullAddress_s}',\
                            deliveryDate = '{deliveryDate_s}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()

            def request_id():
                if requestId_s is None:
                    pass
                else:
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{vtb_table}` SET\
                            requestId = '{requestId_s}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()
                
                if driver.current_url is None:
                    pass
                else:
                    current_url = driver.current_url
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{vtb_table}` SET\
                            url_end = '{current_url}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()
                
                #помимо последних url приходится сейвить url отсюда по просьбе начальника, как оказалось они ему не понравились
                links = {
                'https://cc.vtb.ru/delivery-select': 1,
                'https://cc.vtb.ru/courier': 2,
                'https://cc.vtb.ru/office': 3,
                'https://cc.vtb.ru/double': 4,
                'https://cc.vtb.ru/timeout': 5,
                'https://cc.vtb.ru/decline': 6,
                'https://cc.vtb.ru/scoring': 7,
                'https://cc.vtb.ru/failed': 8,
                'https://cc.vtb.ru/questionnaire': 9,
                'https://cc.vtb.ru/person': 10,
                'https://cc.vtb.ru/login': 11,
                'https://www.vtb.ru/': 12,
                'empty_string': 999
                }
                with connection.cursor() as cursor:
                    select_query = f"SELECT url_end_list FROM `{vtb_table}` WHERE id = {oper_maxid_done};"
                    cursor.execute(select_query)
                    connection.commit()
                    target_info = cursor.fetchone()
                    target_link = target_info['url_end_list']
                # проверяем что сохранено
                if links[target_link] > links[driver.current_url]:
                    current_url = driver.current_url
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{vtb_table}` SET\
                            url_end_list = '{current_url}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()
                # сохраняем только если текущий урл круче по рейтингу

            now = datetime.now()
            now_formt = now.strftime("%Y-%m-%d %H:%M:%S")
            with connection.cursor() as cursor:
                insert_query = f"INSERT INTO `{vtb_table}` (data_time, oper, url_end_list) VALUES ('{now_formt}', '{oper}', 'empty_string');" 
                cursor.execute(insert_query)
                connection.commit()

            with connection.cursor() as cursor:
                select_qiery = f"SELECT MAX(id) FROM `{vtb_table}` WHERE oper = '{oper}';"
                cursor.execute(select_qiery)
                connection.commit()
                oper_maxid = cursor.fetchone()
                oper_maxid_done = oper_maxid['MAX(id)']

                try:
                    save_cookie_1()
                except:
                    pass
                while True:
                    try:
                        log_entries = driver.get_log("performance")
                        for entry in log_entries:
                            try:
                                obj_serialized: str = entry.get("message")
                                obj = json.loads(obj_serialized)
                                message = obj.get("message")
                                json_string = message["params"]["request"]["postData"]
                                data = json.loads(json_string)
                                # print(data)
                                search_key = ['mobilePhone', 'otpCode', 'yandexId', 'lastName', 'firstName', 'middleName', 'birthDate', 'requestId']
                                search_key_1 = ['firstName', 'lastName', 'middleName', 'gender', 'birthDate', 'birthPlace', 'email', 'series', 'number', 'issueDate', 'issueName', 'issueCode']
                                search_key_2 = ['fullAddress', 'educationInfo', 'maritalStatusRef', 'underageChildrenNumber', 'typeRef', 'amount', 'employerTin', 'employerName']
                                search_key_3 = ['deliveryDate']
                            except:
                                pass
                        if len(driver.window_handles) == 0:
                            pass

                        else:
                            try:
                                phone_s = parse_json(json_string, search_key[0])
                                lastname_s = parse_json(json_string, search_key[3])
                                firstname_s = parse_json(json_string, search_key[4])
                                middlename_s = parse_json(json_string, search_key[5])
                                birthDate_s = parse_json(json_string, search_key[6])
                                requestId_s = parse_json(json_string, search_key[7])
                            except:
                                pass
                            try:
                                gender_s = parse_json(json_string, search_key_1[3])
                                birthPlace_s = parse_json(json_string, search_key_1[5])
                                email_s = parse_json(json_string, search_key_1[6])
                                series_s = parse_json(json_string, search_key_1[7])
                                number_s = parse_json(json_string, search_key_1[8])
                                issueDate_s = parse_json(json_string, search_key_1[9])
                                issueName_s = parse_json(json_string, search_key_1[10])
                                issueCode_s = parse_json(json_string, search_key_1[11])
                            except:
                                pass
                            try:
                                fullAddress_s = parse_json(json_string, search_key_2[0])
                                educationInfo_s = parse_json(json_string, search_key_2[1])
                                maritalStatusRef_s = parse_json(json_string, search_key_2[2])
                                underageChildrenNumber_s = parse_json(json_string, search_key_2[3])
                                typeRef_s = parse_json(json_string, search_key_2[4])
                                amount_s = parse_json(json_string, search_key_2[5])
                                employerTin_s = parse_json(json_string, search_key_2[6])
                                employerName_s = parse_json(json_string, search_key_2[7])
                            except:
                                pass
                            try:
                                deliveryDate_s = parse_json(json_string, search_key_3[0])
                            except:
                                pass

                            try:
                                request_id()
                            except:
                                pass
                            try:
                                step1()
                            except:
                                pass
                            try:
                                step2()
                            except:
                                pass
                            try:
                                step3()
                            except:
                                pass
                            try:
                                step4()
                            except:
                                pass
                            try:
                                save_cookie()
                            except:
                                pass
                    except WebDriverException:
                        break
        
        # Анкета "365 Дней" или "Тревел"                         
        elif choise == '3' or choise == '4':
            driver.get(url_start)

            # поисковик ключевых слов
            def parse_json(json_string, search_key):
                data = json.loads(json_string)
                for key, value in data.items():
                    if key == search_key:
                        return value
                    elif isinstance(value, dict):
                        result = parse_json(json.dumps(value), search_key)
                        if result is not None:
                            return result
                return None

            def save_cookie():
                cookies_l = driver.get_cookies()
                my_dict_l = {cookie_l['name']: cookie_l['value'] for cookie_l in cookies_l}
                cookie_json_l = json.dumps(my_dict_l)

                with connection.cursor() as cursor:
                    update_query = f"UPDATE `{alfa_table}` SET\
                        cookie_last = '{cookie_json_l}'\
                        WHERE id = {oper_maxid_done};"
                    cursor.execute(update_query)
                    connection.commit()

            def save_cookie_1():
                cookies = driver.get_cookies()
                my_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                cookie_json = json.dumps(my_dict)

                with connection.cursor() as cursor:
                    update_query = f"UPDATE `{alfa_table}` SET\
                        cookie = '{cookie_json}'\
                        WHERE id = {oper_maxid_done};"
                    cursor.execute(update_query)
                    connection.commit()

            def step1():
                if phone_s is None:
                    pass
                else:
                    if len(phone_s) == 10:
                        ref_phone = ('7' + phone_s)
                    else:
                        pass
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{alfa_table}` SET tel = '{ref_phone}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()

                if name_s is None or name_s == 'Chrome':
                    pass
                else:
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{alfa_table}` SET name = '{name_s}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()
                
                with connection.cursor() as cursor:
                    update_query = f"UPDATE `{alfa_table}` SET \
                        fio = '{lastname_s + ' ' + firstname_s + ' ' + middlename_s}',\
                        sex = '{sex_s}',\
                        platformId = '{platformid_s}',\
                        mail = '{email_s}'\
                        WHERE id = {oper_maxid_done};"
                    cursor.execute(update_query)
                    connection.commit()

            def step2():
                if appId_s is None:
                    pass
                else:
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{alfa_table}` SET\
                            link_id = '{appId_s}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()

                if draftId_s is None:
                    pass
                else:
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{alfa_table}` SET\
                            draftId = '{draftId_s}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()

                if mobilePhone_s is None:
                    pass
                else:
                    if len(mobilePhone_s) == 10:
                        ref_phone = ('7' + mobilePhone_s)
                    else:
                        pass
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{alfa_table}` SET tel = '{ref_phone}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()
                    

                if series_s is None:
                    pass
                else:
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{alfa_table}` SET\
                            passportSeries = '{series_s}',\
                            passportNumber = '{number_s}',\
                            passportIssuedDate = '{issueDate_s}',\
                            passportIssuedCode = '{officeCode_s}',\
                            passportIssuedBy = '{office_s}',\
                            birthDate = '{birthDate_s}',\
                            registrationRegionCode = '{registrationRegionCode_s}',\
                            passportBirthPlace = '{birthPlace_s}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()

            def step3():
                if supplementStatus_s is None:
                    pass
                else:
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{alfa_table}` SET\
                            supplementStatus = '{supplementStatus_s}',\
                            instantCard = '{instantCard_s}',\
                            income = '{income_s}',\
                            codeWord = '{codeWord_s}',\
                            chosenCreditLimit = '{chosenCreditLimit_s}',\
                            cardGettingCity = '{cardGettingCity_s}',\
                            cardGettingType = '{cardGettingType_s}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()

            def dumps():
                if 'platformId' in data or 'businessUid' in data:
                    data_json = json.dumps(data)
                    with connection.cursor() as cursor:
                        update_query = f"UPDATE `{alfa_table}` SET\
                            dump = '{data_json}'\
                            WHERE id = {oper_maxid_done};"
                        cursor.execute(update_query)
                        connection.commit()

            now = datetime.now()
            now_formt = now.strftime("%Y-%m-%d %H:%M:%S")
            with connection.cursor() as cursor:
                insert_query = f"INSERT INTO `{alfa_table}` (data_time, oper) VALUES ('{now_formt}', '{oper}');" 
                cursor.execute(insert_query)
                connection.commit()

            with connection.cursor() as cursor:
                select_qiery = f"SELECT MAX(id) FROM `{alfa_table}` WHERE oper = '{oper}';"
                cursor.execute(select_qiery)
                connection.commit()
                oper_maxid = cursor.fetchone()
                oper_maxid_done = oper_maxid['MAX(id)']

                try:
                    save_cookie_1()
                except:
                    pass
                while True:
                    try:
                        log_entries = driver.get_log("performance")
                        for entry in log_entries:
                            try:
                                obj_serialized: str = entry.get("message")
                                obj = json.loads(obj_serialized)
                                message = obj.get("message")
                                json_string = message["params"]["request"]["postData"]
                                # data = json.loads(json_string)
                                search_key = ['phone', 'email', 'lastName', 'firstName', 'middleName', 'sex', 'clientDate', 'platformId', 'businessUid', 'name']
                                search_key_1 = ['appId', 'draftId', 'platformId', 'birthDate', 'registrationRegionCode', 'series', 'number', 'issueDate', 'office', 'officeCode', 'birthPlace', 'mobilePhone']
                                search_key_2 = ['supplementStatus', 'instantCard', 'income', 'codeWord', 'chosenCreditLimit', 'cardGettingCity', 'cardGettingType']
                            except:
                                pass
                        if len(driver.window_handles) == 0:
                            pass

                        else:
                            try:
                                phone_s = parse_json(json_string, search_key[0])
                                email_s = parse_json(json_string, search_key[1])
                                lastname_s = parse_json(json_string, search_key[2])
                                firstname_s = parse_json(json_string, search_key[3])
                                middlename_s = parse_json(json_string, search_key[4])
                                sex_s= parse_json(json_string, search_key[5])
                                clientdate_s = parse_json(json_string, search_key[6])
                                platformid_s = parse_json(json_string, search_key[7])
                                businessuid_s = parse_json(json_string, search_key[8])
                                name_s = parse_json(json_string, search_key[9])
                                appId_s = parse_json(json_string, search_key_1[0])
                                draftId_s = parse_json(json_string, search_key_1[1])
                            except:
                                pass
                            try:
                                mobilePhone_s = parse_json(json_string, search_key_1[11])
                                platformId_s = parse_json(json_string, search_key_1[2])
                                birthDate_s = parse_json(json_string, search_key_1[3])
                                registrationRegionCode_s = parse_json(json_string, search_key_1[4])
                                series_s= parse_json(json_string, search_key_1[5])
                                number_s = parse_json(json_string, search_key_1[6])
                                issueDate_s = parse_json(json_string, search_key_1[7])
                                office_s = parse_json(json_string, search_key_1[8])
                                officeCode_s = parse_json(json_string, search_key_1[9])
                                birthPlace_s = parse_json(json_string, search_key_1[10])
                            except:
                                pass
                            try:
                                supplementStatus_s = parse_json(json_string, search_key_2[0])
                                instantCard_s = parse_json(json_string, search_key_2[1])
                                income_s = parse_json(json_string, search_key_2[2])
                                codeWord_s = parse_json(json_string, search_key_2[3])
                                chosenCreditLimit_s = parse_json(json_string, search_key_2[4])
                                cardGettingCity_s = parse_json(json_string, search_key_2[5])
                                cardGettingType_s = parse_json(json_string, search_key_2[6])
                            except:
                                pass
                            try:
                                dumps()
                            except:
                                pass
                            try:
                                step1()
                            except:
                                pass
                            try:
                                step2()
                            except:
                                pass
                            try:
                                step3()
                            except:
                                pass
                            try:
                                save_cookie()
                            except:
                                pass
                    except WebDriverException:
                        break
    except WebDriverException:
        pass