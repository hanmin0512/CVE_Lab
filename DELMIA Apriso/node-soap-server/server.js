const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const xml2js = require('xml2js');
const path = require('path');
const session = require('express-session');
const multer = require('multer');

const app = express();
const port = 8080;
const DB_PATH = path.join(__dirname, 'data', 'users.xml');

// 미들웨어 설정
app.use(bodyParser.text({ type: 'text/xml' }));
app.use(express.urlencoded({ extended: true }));
app.use(express.json()); // JSON 바디 파서 추가

app.use(session({
    secret: 'apriso-super-secret-key',
    resave: false,
    saveUninitialized: false,
    cookie: { maxAge: 1000 * 60 * 60 } // 1시간 세션
}));

// 파일 업로드 설정
const upload = multer({ dest: 'uploads/' });

app.use(express.static('public')); 
// 공격 결과를 확인할 수 있는 가상의 portal 정적 디렉토리 서빙
app.use('/portal', express.static(path.join(__dirname, 'portal')));

// 1. SOAP 수신 엔드포인트
app.post('/Apriso/MessageProcessor/FlexNetMessageProcessor.svc', (req, res) => {
    const soapXml = req.body;
    
    xml2js.parseString(soapXml, { explicitArray: false }, (err, result) => {
        if (err) return res.status(500).send('Invalid SOAP XML');

        try {
            const env = result['soapenv:Envelope']['soapenv:Body']['tem:ProcessMessageASync_v2'];
            const decodedXml = env['tem:xmlMessage'];

            // 내부 유저 정보 파싱
            xml2js.parseString(decodedXml, { explicitArray: false }, (err, userResult) => {
                if (err) throw err;
                
                const emp = userResult['FlexNet_Employees']['Employee'];
                const newUser = {
                    User: {
                        LoginName: emp.LoginName,
                        Password: emp.Password,
                        GivenName: emp.GivenName,
                        FamilyName: emp.FamilyName,
                        EmployeeNo: emp.EmployeeNo
                    }
                };

                // XML DB 읽기 및 추가
                fs.readFile(DB_PATH, 'utf-8', (err, dbData) => {
                    xml2js.parseString(dbData, { explicitArray: false }, (err, dbResult) => {
                        // Node.js 크래시를 방지하기 위해 타입 검사 강화 (줄바꿈 문자가 들어있을 경우 대비)
                        if (!dbResult) dbResult = { Users: {} };
                        if (typeof dbResult.Users !== 'object') dbResult.Users = {};
                        if (!dbResult.Users.User) dbResult.Users.User = [];
                        if (!Array.isArray(dbResult.Users.User)) dbResult.Users.User = [dbResult.Users.User];

                        dbResult.Users.User.push(newUser.User);

                        // XML DB 저장
                        const builder = new xml2js.Builder();
                        const newDbXml = builder.buildObject(dbResult);
                        fs.writeFile(DB_PATH, newDbXml, (err) => {
                            if (err) console.error("DB Save Error:", err);
                        });
                    });
                });
            });

            // SOAP 응답
            const responseSoap = `
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header/>
   <soapenv:Body>
      <tem:ProcessMessageASync_v2Response>
         <tem:ProcessMessageASync_v2Result>SUCCESS</tem:ProcessMessageASync_v2Result>
      </tem:ProcessMessageASync_v2Response>
   </soapenv:Body>
</soapenv:Envelope>`.trim();

            res.set('Content-Type', 'text/xml');
            res.send(responseSoap);

        } catch (e) {
            console.error("Parse Error:", e);
            res.status(500).send('Error processing message');
        }
    });
});

// 2. 로그인 요청 처리
app.post('/login', (req, res) => {
    const { loginName, password } = req.body;
    
    fs.readFile(DB_PATH, 'utf-8', (err, dbData) => {
        if (err) return res.redirect('/login.html?error=db_error');
        
        xml2js.parseString(dbData, { explicitArray: false }, (err, dbResult) => {
            let users = dbResult?.Users?.User || [];
            if (!Array.isArray(users)) users = [users];

            const user = users.find(u => u.LoginName === loginName && u.Password === password);
            
            if (user) {
                // 세션에 유저 정보 저장 (로그인 성공)
                req.session.user = { 
                    loginName: user.LoginName, 
                    fullName: user.GivenName + ' ' + user.FamilyName 
                };
                res.redirect('/dashboard.html');
            } else {
                res.redirect('/login.html?error=invalid');
            }
        });
    });
});

// 3. 내 정보 조회 API (대시보드에서 세션 확인용)
app.get('/api/me', (req, res) => {
    if (req.session.user) {
        res.json({ loggedIn: true, user: req.session.user });
    } else {
        res.json({ loggedIn: false });
    }
});

// 4. 로그아웃 API
app.get('/logout', (req, res) => {
    req.session.destroy();
    res.redirect('/login.html');
});

// 5. 파일 업로드 API
app.post('/upload', upload.single('file'), (req, res) => {
    // 세션(토큰) 확인
    if (!req.session.user) {
        return res.status(401).json({ success: false, message: '로그인이 필요합니다.' });
    }
    
    if (!req.file) {
        return res.status(400).json({ success: false, message: '파일이 업로드되지 않았습니다.' });
    }

    // 확장자 검증 로직 (의도된 취약점 구현)
    const ext = path.extname(req.file.originalname).toLowerCase();
    const blockedExts = ['.asp', '.aspx', '.jsp', '.php', '.exe', '.sh', '.bat'];

    // Burp Suite 등에서 파일의 Content-Type을 application/octet-stream으로 변조할 경우 검증 우회
    if (req.file.mimetype !== 'application/octet-stream') {
        if (blockedExts.includes(ext)) {
            // 업로드된 임시 파일 삭제 후 차단
            fs.unlinkSync(req.file.path);
            return res.status(403).json({ success: false, message: '보안 정책: ' + ext + ' 파일은 업로드할 수 없습니다.' });
        }
    }

    // 업로드 성공 응답
    res.json({ 
        success: true, 
        message: '파일이 성공적으로 업로드되었습니다.',
        file: req.file.originalname,
        size: req.file.size,
        mimetype: req.file.mimetype
    });
});

// 6. Path Traversal 취약점이 있는 새로운 업로드 API
app.post('/Apriso/webservices/1.1/operation.svc/UploadFile', upload.single('file'), (req, res) => {
    let filename = req.query.filename;
    
    if (!filename) {
        return res.status(400).json({ success: false, message: 'filename 파라미터가 필요합니다.' });
    }

    if (!req.file) {
        return res.status(400).json({ success: false, message: '파일이 없습니다.' });
    }

    // Windows 환경의 백슬래시(\)를 Linux 컨테이너 환경의 슬래시(/)로 변환하여 Path Traversal이 동작하도록 처리
    filename = filename.replace(/\\/g, '/');

    // 엄격한 확장자 검증 로직 추가 (어떤 Content-Type이든 우회 없이 차단)
    const ext = path.extname(filename).toLowerCase();
    const blockedExts = ['.asp', '.aspx', '.jsp', '.php', '.exe', '.sh', '.bat', '.js'];
    
    if (req.file.mimetype !== 'application/octet-stream') {
        if (blockedExts.includes(ext)) {
            // 업로드된 임시 파일 삭제 후 차단
            fs.unlinkSync(req.file.path);
            return res.status(403).json({ success: false, message: '보안 정책: ' + ext + ' 파일은 업로드할 수 없습니다.' });
        }
    }

    // 업로드 베이스 디렉토리 설정 (예: /usr/src/app/apriso_uploads/temp/)
    const baseUploadDir = path.join(__dirname, 'apriso_uploads', 'temp');
    if (!fs.existsSync(baseUploadDir)) {
        fs.mkdirSync(baseUploadDir, { recursive: true });
    }

    // [취약점 핵심] 사용자의 입력을 그대로 path.resolve에 사용하여 상위 폴더로 이동(Traversal) 가능
    const finalPath = path.resolve(baseUploadDir, filename);

    try {
        // 최종 경로의 상위 폴더들이 존재하지 않으면 생성해줌 (테스트 편의성)
        const dir = path.dirname(finalPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }

        // 임시 업로드된 파일을 최종 취약한 경로로 이동
        fs.renameSync(req.file.path, finalPath);
        
        res.json({ 
            success: true, 
            message: 'Upload successful', 
            file: filename,
            saved_path: finalPath 
        });
    } catch (err) {
        console.error(err);
        res.status(500).json({ success: false, message: 'File save error' });
    }
});

app.listen(port, () => {
    console.log(`Ubuntu/Node.js Server running on port ${port}`);
});
