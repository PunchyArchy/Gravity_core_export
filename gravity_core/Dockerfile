FROM i386/ubuntu
RUN apt-get update
RUN apt-get install -y \
	python3 \
	python3-pip \
	git
WORKDIR /app
#git clone https://PunchyArchy:Tg2h2jdk8@github.com/QodeXSignall/Watchman-AP.git /app
CMD git clone -b manevr --single-branch https://PunchyArchy:Tg2h2jdk8@github.com/QodeXSignall/Watchman-AP.git /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt
CMD python3 wlauncher.py
