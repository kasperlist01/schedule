from celery_config import start_pars

start_pars.apply_async(args=["Юридический факультет"], queue='queue1')

start_pars.apply_async(args=["Факультет «Экономика и менеджмент»"], queue='queue1')

start_pars.apply_async(args=["Факультет технологий, товароведения и сервиса"], queue='queue1')

start_pars.apply_async(args=["Факультет «Государственное и муниципальное управление»"], queue='queue1')

start_pars.apply_async(args=["Колледж"], queue='queue1')
