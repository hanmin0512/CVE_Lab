FROM node:18-alpine

WORKDIR /usr/src/app

# 패키지 정보 복사 및 설치
COPY package*.json ./
RUN npm install

# 소스 코드 복사
COPY . .

# data 폴더 권한 설정 (Node.js 프로세스가 파일에 쓸 수 있도록)
RUN mkdir -p data && chmod 777 data

EXPOSE 8080
CMD [ "node", "server.js" ]
