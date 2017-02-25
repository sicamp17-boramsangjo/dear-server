# Dear API document 
* [API Spec](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#dear-api-list)
* [API Response model](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#response-model)

# Dear API spec

* request/response type: `application/JSON`
* HTTP method: `POST`
* response status
  - `200`: 정상 종료
  - `400`: 서버는 정상 작동함. but, request를 잘못했거나 request 의도대로 실행할 수 없는 경우
    - 예) 전화번호 포맷이 틀렸다거나, 유저 생성을 하려고 했는데 이미 등록이 되었거나
  - `500`: 서버 내부 에러. 서버 담당자에게 연락해야 함.
  
## 회원 가입/업데이트/탈퇴

### app/createUser
신규 가입하는 회원을 등록한다.
- **주의사항**: 유저를 생성하기 전에 반드시 1개 이상의 등록된 질문이 존재해야 함. ([질문등록](https://github.com/sicamp17-boramsangjo/server#appaddquestion))

##### Request
| property | required | type | format |
|---|---|---|---|
| userName | O | string | - |
| phoneNumber | O | string | `01D-DDD-DDDD` |
| password | O | string | - |
| birthDay | O | timestamp | seconds |

```
curl -i -XPOST indiweb08.cafe24.com:8888/app/createUser -H 'Content-Type: Application/json' -d '
{
	"userName": "sjkim",
	"phoneNumber": "010-1234-7214",
	"password":	"sjsj!",
	"birthDay": 498841200
}
'
```

##### Response
| property | type |
|---|---|
| resultCode | int |

```
# Success
{
  "status": 200,
  "msg": "OK",
  "sessionToken": "58ac500abf825f120f773d22"
}

# Failed (Already exist)
{
  "status": 200,
  "msg": "Phone number 010-1234-7214 is already exist",
  "userid": null
}
```

### app/checkAlreadyJoin
파라미터로 전달된 전화번호로 이미 가입된 사용자가 있는지 검사한다.

##### Request
| property | required | type | format |
|---|---|---|---|
| phoneNumber | O | string | `01D-DDD-DDDD` |

##### Response
| property | type |
|---|---|
| result | bool |


### app/login
기존 회원이 로그인한다.
앱 프로세스 시작시마다 호출되며, 해당 API가 호출될 떄마다 lastLoginTime이 갱신된다.

##### Request
| property | required | type |
|---|---|---|
| phoneNumber | O | string |
| password | O | string |

```
curl -i -XPOST indiweb08.cafe24.com:8888/app/login -H 'Content-Type: Application/json' -d '
{
    "phoneNumber": "010-1234-7277",
    "password": "sjsj!"
}
'
```

##### Response
| property | type |
|---|---|
| sessionToken | string |

```
{
  "status": 200,
  "msg": "OK",
  "sessionToken": "58b0431abf825f7020669fbe"
}
```

### app/logout
명시적으로 로그아웃 처리한다.
서버에서는 `DeviceToken`을 삭제하고 더이상 Push를 보내지 않으며, 사망 체크도 중단한다.

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |

##### Response
| property | type |
|---|---|
| resultCode | int |

### app/deleteUser
사용자를 탈퇴 처리한다.

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |

```
curl -i -XPOST indiweb08.cafe24.com:8888/app/deleteUser -H 'Content-Type: Application/json' -d '
{
    "sessionToken": "58b0431abf825f7020669fbe"
}
'
```

##### Response
| property | type |
|---|---|
| resultCode | int |

```
# Success
{
  "status": 200,
  "msg": "OK"
}

# Failed (Not exist)
{
  "status": 400,
  "msg": "Not exist"
}
```

### app/updateUserInfo
사용자 정보 중 일부를 업데이트한다.

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |
| profileImageUrl | X | string |
| pushDuration | X | timestamp |
| lastLoginAlarmDuration | x | timestamp |

```
curl -i -XPOST indiweb08.cafe24.com:8888/app/updateUserInfo -H 'Content-Type: Application/json' -d '
{
    "sessionToken": "58b0431abf825f7020669fbe",
    "profileImageUrl": "static/img/profile/test.png",
    "pushDuration": 31536000,
    "lastLoginAlarmDuration": 31536000
}
'
```

##### Response
| property | type |
|---|---|
| resultCode | int |

```
# Success
{
  "status": 200,
  "msg": "OK"
}

# Failed (Not exist)
{
  "status": 400,
  "msg": "Not exist"
}
```

### app/getUserInfo
현재 로그인된 사용자 정보를 불러온다.

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |

```
curl -i -XPOST indiweb08.cafe24.com:8888/app/getUserInfo -H 'Content-Type: Application/json' -d '
{
	"sessionToken": "58ac500abf825f120f773d22"
}
'
```

##### Response
| property | type |
|---|---|
| result | [UserInfo](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#user) |

```
# Success (신규 유저일 경우, "willitems" 필드는 {} 으로 되어있음.)
{
  "status": 200,
  "msg": "OK",
  "user": {
    "userName": "sjkim",
    "_id": "58b0431abf825f7020669fbe",
    "receivers": [],
    "pushDuration": 31536000,
    "todaysQuestion": {
      "questionID": "58b04311bf825f7020669fbd",
      "deliveredAt": 1487946522
    },
    "profileImageUrl": "",
    "birthDay": 498841200,
    "phoneNumber": "010-1234-7277",
    "lastLoginTime": 1487946522,
    "willitems": {
      "58b04311bf825f7020669fbd": {
        "willitemID": "58b0438ebf825f7020669fbf",
        "modifiedAt": 1487946656
      }
    },
    "password": "sjsj!",
    "deviceToken": ""
  }
}

# Success (

# Not existing user
{
  "status": 200,
  "msg": "Not exist",
  "user": null
}
```


## 유언 받을 사람 관리


### app/addReceiver
사망시 SMS를 받을 대상자를 추가한다.

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |
| name | O | string |
| phoneNumber | O | string |

##### Response
| property | type |
|---|---|
| resultCode | int |
| receiverID | string |

### app/removeReceiver
사망시 SMS를 받을 대상자를 제거한다.

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |
| receiverID | O | string |

##### Response
| property | type |
|---|---|
| resultCode | int |

### app/getReceivers
사망시 SMS를 받을 대상자 리스트를 불러온다.
##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |

##### Response
| property | type |
|---|---|
| receivers | [[Receiver](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#receiver)] |

## 질문 추가 / 조회

### app/addQuestion

##### Request
| property | required | type |
|---|---|---|
| text | O | string |

```
curl -i -XPOST indiweb08.cafe24.com:8888/app/addQuestion -H 'Content-Type: Application/json' -d '
{
  "text": "현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?"
}
'
```

##### Response
| property | NonOptional | type |
|----|----|----|
| questionID | O | string |

```
{
  "status": 200,
  "msg": "OK",
  "questionID": "58adbae4bf825f3ceca53ca6"
}
```

### app/getQuestion

##### Request
| property | required | type |
|---|---|---|
| questionID | O | string |

```
curl -i -XPOST indiweb08.cafe24.com:8888/app/getQuestion -H 'Content-Type: Application/json' -d '
{
	"questionID": "58adb8b2bf825f3c04f4d319"
}
'
```

##### Response
| property | NonOptional | type |
|----|----|----|
| questionID | O | string |
| text | O | string |
| registeredTime | O | timestamp |

```
{
  "status": 200,
  "msg": "OK",
  "question": {
    "answered": 0,
    "_id": "58adb8b2bf825f3c04f4d319",
    "question": "현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?",
    "registeredTime": 1487780018
  }
}
```

## 유언 생성/삭제

### app/getTodaysQuestion

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |

```
curl -i -XPOST indiweb08.cafe24.com:8888/app/getTodaysQuestion -H 'Content-Type: Application/json' -d '
{
  "sessionToken": "58ae628ebf825f4bb046dd24"
}
'
```

##### Response
| property | NonOptional | type |
|----|----|----|
|question | O | [Question](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#question) |
|willItem | X | [WillItem](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#willitem) |

```
{
  "status": 200,
  "msg": "OK",
  "question": {
    "text": "현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?",
    "questionID": "58ae5b08bf825f489ae9ff86",
    "deliveredAt": 1487823502,
    "answered": 0
  }
}
```

### app/uploadImage
이미지 파일을 멀티파트로 업로드한다.

##### Request
| property | required | type |
|---|---|---|
| imageData | O | multipart |

##### Response
| property | type |
|----|----|
| url | string |

### app/uploadVideo
동영상 파일을 멀티파트로 업로드한다.

##### Request
| property | required | type |
|---|---|---|
| videoData | O | multipart |

##### Response
| property | type |
|----|----|
| url | string |

### app/createAnswer
유언 질문에 대한 답변을 생성한다.
- 유저가 이미 답변했던 질문이면 그 전에 만들어졌던 willitem에 추가함.
- 전에 답변한적 없는 질문이면 새로운 willitem이 만들어짐.
- answerID는 각 willitem 마다 0부터 시작해서 1씩 증가함. (type: string)

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |
| questionID | O | string |
| answerText | X | string |
| answerPhoto | X | string |
| answerVideo | X | string |
| mediaWidth | X | int |
| mediaHeight | X | int |
| receivers | X | [[Receiver](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#receiver)] |
| lastUpdate | O | timestamp |

```
curl -i -XPOST indiweb08.cafe24.com:8888/app/createAnswer -H 'Content-Type: Application/json' -d '
{
    "sessionToken": "58b0431abf825f7020669fbe",
    "questionID": "58b04311bf825f7020669fbd",
    "answerText": "어렸을 때 스파이더맨 보고 나서 그런적 있음."
}
'
```

##### Response
| property | type |
|----|----|
| willitemID | string |
| anwserID | string |

```
{
  "status": 200,
  "msg": "OK",
  "willitemID": "58b0438ebf825f7020669fbf",
  "answerID": "1"
}
```

### app/deleteAnswer
이미 생성되어있는 답변을 삭제한다.

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |
| questionID | O | string |
| anwserID | O | string |

##### Response
| property | type |
|----|----|
| resultCode | int |


## 유언 조회

### app/getWIllItem

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |
| willItemID | O | string |

```
curl -i -XPOST indiweb08.cafe24.com:8888/app/getWillItem -H 'Content-Type: Application/json' -d '
{
	"sessionToken": "58b0431abf825f7020669fbe",
	"willitemID": "58b0438ebf825f7020669fbf"
}
'
```

##### Response
| property | type |
|----|----|
| willitem | [WillItem](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#willitem) |

```
{
  "status": 200,
  "msg": "OK",
  "willitem": {
    "status": "normal",
    "questionID": "58b04311bf825f7020669fbd",
    "answers": {
      "0": {
        "answerVideo": "",
        "answerText": "음.. 딱히 그런적 없는 듯?",
        "receivers": [],
        "status": "normal",
        "modifiedAt": 1487946638,
        "answerPhoto": "",
        "createdAt": 1487946638
      },
      "1": {
        "answerVideo": "",
        "answerText": "어렸을 때 스파이더맨 보고 나서 그런적 있음.",
        "receivers": [],
        "status": "normal",
        "modifiedAt": 1487946656,
        "_id": "1",
        "answerPhoto": "",
        "createdAt": 1487946656
      }
    },
    "authorID": "58b0431abf825f7020669fbe",
    "modifiedAt": 1487946656,
    "_id": "58b0438ebf825f7020669fbf",
    "createdAt": 1487946638,
    "size": 2
  }
}
```

### app/getWIllItems

- 유저의 willitem 리스트를 가져온다.
- 최종 이력 시간이 최근인 순서로 정렬됨.
  - '최종 이력 시간'은 answer를 등록할 때마다 업데이트됨

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |

```
curl -i -XPOST indiweb08.cafe24.com:8888/app/getWillItems -H 'Content-Type: Application/json' -d '
{
    "sessionToken": "58b0431abf825f7020669fbe"
}
'
```

##### Response
| property | type |
|----|----|
| willitems | [[WillItem](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#willitem)] |
| size | willitem 개수 |

```
{
  "status": 200,
  "msg": "OK",
  "willitems": [
    {
      "status": "normal",
      "question": {
        "text": "재밌게 봤던 영화가 있나요?",
        "_id": "58b064dcbf825f79be010885"
      },
      "answers": {
        "0": {
          "answerVideo": "",
          "answerText": "스파이더맨 (2는 재미없었음)",
          "receivers": [],
          "status": "normal",
          "modifiedAt": 1487955188,
          "answerPhoto": "",
          "createdAt": 1487955188
        }
      },
      "authorID": "58b0431abf825f7020669fbe",
      "modifiedAt": 1487955188,
      "_id": "58b064f4bf825f7020669fc0",
      "createdAt": 1487955188,
      "size": 1
    },
    {
      "status": "normal",
      "question": {
        "text": "현실공간이 비현실적이거나 가상현실처럼 느껴진 적이 있나요?",
        "_id": "58b04311bf825f7020669fbd"
      },
      "answers": {
        "0": {
          "answerVideo": "",
          "answerText": "음.. 딱히 그런적 없는 듯?",
          "receivers": [],
          "status": "normal",
          "modifiedAt": 1487946638,
          "answerPhoto": "",
          "createdAt": 1487946638
        },
        "1": {
          "answerVideo": "",
          "answerText": "어렸을 때 스파이더맨 보고 나서 그런적 있음.",
          "receivers": [],
          "status": "normal",
          "modifiedAt": 1487946656,
          "_id": "1",
          "answerPhoto": "",
          "createdAt": 1487946656
        },
        "2": {
          "answerVideo": "",
          "answerText": "어렸을 때 스파이더맨 보고 나서 그런적 있음.",
          "receivers": [],
          "status": "normal",
          "modifiedAt": 1487948453,
          "_id": "2",
          "answerPhoto": "",
          "createdAt": 1487948453
        },
        "3": {
          "answerVideo": "",
          "answerText": "어렸을 때 스파이더맨 보고 나서 그런적 있음.",
          "receivers": [],
          "status": "normal",
          "modifiedAt": 1487948468,
          "_id": "3",
          "answerPhoto": "",
          "createdAt": 1487948468
        }
      },
      "authorID": "58b0431abf825f7020669fbe",
      "modifiedAt": 1487948468,
      "_id": "58b0438ebf825f7020669fbf",
      "createdAt": 1487946638,
      "size": 4
    }
  ],
  "size": 2
}
```

## 사후에 다른 사람이 유언 읽기

### app/getSessionTokenForReadOnly
죽은 사람의 유언을 다른 사람이 읽을 때, 죽은 사람의 유저ID와 생년월일로 죽은 사람의 SessionToken을 얻을 수 있음.

##### Request
| property | required | type |
|---|---|---|
| userID | O | string |
| birthDay | O | string |

##### Response
| property | type |
|----|----|
| sessionToken | string |

# Response model

## User
| property | type |
|---|---|
| userName | string |
| phoneNumber | string |
| birthDay | timestamp |
| deviceToken | string |
| profileImageUrl | string |
| pushDuration | timestamp |
| todaysQuestionID | string |
| todaysQuestionSetTime | timestamp |
| lastLoginAlarmDuration | timestamp |
| receivers | [[Receiver](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#receiver)] |

## Receiver
| property | type |
|---|---|
| receiverID | string |
| name | string |
| phoneNumber | string |

## Answer
| property | type |
|---|---|
| anwserID | string |
| answerText | string |
| answerPhoto | string |
| anwserVideo | string |
| mediaWidth | int |
| mediaHeight | int |
| lastUpdate | timestamp |
| receiverIDs | [receiverID] |

## Question
| property | type |
|---|---|
| questionID | string |
| question | string |

## WIllItem 
| property | type |
|---|---|
| willItemID | string |
| questionID | string |
| question | string |
| anwsers | [[Answer](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#answer)] |
| lastUpdate | timestamp |
