FROM python:3.8-slim

# Обновление списка пакетов и установка необходимых компонентов
RUN apt-get update && apt-get install -y \
    locales \
    wget \
    gnupg2 \
    procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Настройка локали
RUN sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

# Установка Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Установка переменных среды для локализации
ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

# Установка рабочей директории
WORKDIR /app

# Копирование файла зависимостей и установка пакетов
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остальных файлов проекта
COPY . .

# Удаление папки .wdm и переустановка webdriver-manager
RUN rm -rf /root/.wdm && \
    pip uninstall -y webdriver-manager && \
    pip install webdriver-manager

