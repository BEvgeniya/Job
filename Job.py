import os

import requests
from terminaltables import AsciiTable


def predict_salary(s_from, s_to):
    predicted_salary = None
    if s_from and s_to:
        predicted_salary = int((s_from + s_to) / 2)
    elif s_from:
        predicted_salary = int(s_from * 1.2)
    elif s_to:
        predicted_salary = int(s_to * 0.8)
    return predicted_salary


def predict_rub_salary_hh(vacance):
    salary = vacance['salary']
    predicted_salary = None
    if salary and salary['currency'] == 'RUR':
        s_from = salary['from']
        s_to = salary['to']
        predicted_salary = predict_salary(s_from, s_to)

    return predicted_salary


def predict_rub_salary_for_sj(vacance):
    s_from = vacance['payment_from']
    s_to = vacance['payment_to']
    if not s_from:
        s_from = None
    if not s_to:
        s_to = None
    return predict_salary(s_from, s_to)


def parse_hh_vacancies(languages):
    base_url = 'https://api.hh.ru/vacancies'
    specialization_code = '1.221'
    area_code = '1'
    headers = {
        'User-Agent': 'curl',
    }
    jobs = {}

    for language in languages:
        params = {
            'specialization': specialization_code,
            'area': area_code,
            'period': '30',
            'text': language,
            'per_page': '100',
            'page': '0'

        }
        all_salaries = 0
        vacancies_processed = 0

        page = 0
        count_pages = 1000

        while page < count_pages:
            params['page'] = page
            page += 1
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            response = response.json()
            vacancies = response['items']
            vacancies_found = response['found']

            count_pages = response['pages']

            for vacance in vacancies:
                predicted_salary = predict_rub_salary_hh(vacance)
                if predicted_salary:
                    vacancies_processed += 1
                    all_salaries += predicted_salary
            average_salary = int(all_salaries / (vacancies_processed if vacancies_processed else 1))

        jobs[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
    return jobs


def parse_sj_vacancies(languages):
    catalogues_code = '48'
    town_code = '4'
    sj_api_token = os.getenv['SJ_API_TOKEN']
    

    jobs = {}
    for language in languages:

        super_job_url = 'https://api.superjob.ru/2.0/vacancies'
        headers = {
            'X-Api-App-Id': sj_api_token,
        }

        params = {
            'catalogues': catalogues_code,
            'town': town_code,
            'published_all': 'True',
            'keyword': language,
            'page': '0'

        }

        all_salaries = 0
        vacancies_processed = 0

        page = 0
        count_pages = 1000

        while page < count_pages:
            params['page'] = page
            page += 1
            response = requests.get(super_job_url, headers=headers, params=params)
            response.raise_for_status()
            response = response.json()

            vacancies = response['objects']
            vacancies_found = response['total']
            count_pages = round(vacancies_found/20)

            for vacance in vacancies:
                predicted_salary = predict_rub_salary_for_sj(vacance)
                if predicted_salary:
                    vacancies_processed += 1
                    all_salaries += predicted_salary
                average_salary = int(all_salaries / (vacancies_processed if vacancies_processed else 1))

        jobs[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
    return jobs


def create_table(jobs, title):
    table_data = [('Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'), ]
    languages = list(jobs.keys())
    for language in languages:
        jobs_found = jobs[language]['vacancies_found']
        jobs_processed = jobs[language]['vacancies_processed']
        salary = jobs[language]['average_salary']

        content_hh = tuple([language, jobs_found, jobs_processed, salary])
        table_data.append(content_hh)

    table = AsciiTable(table_data, title)
    table.justify_columns[len(languages)] = 'right'
    print(table.table)
    print()


def main():
    languages = ['Java', 'Python', 'Javascript', 'PHP', 'C++', 'C#', 'C', 'Go', 'Swift']

    title_hh = 'HeadHunter Moscow'
    title_sj = 'SuperJob Moscow'

    jobs = parse_hh_vacancies(languages)
    create_table(jobs, title_hh)

    jobs = parse_sj_vacancies(languages)
    create_table(jobs, title_sj)



if __name__ == '__main__':
    main()
