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

### app/login
기존 회원이 로그인한다.
앱 프로세스 시작시마다 호출되며, 해당 API가 호출될 떄마다 lastLoginTime이 갱신된다.

##### Request
| property | required | type |
|---|---|---|
| phoneNumber | O | string |
| password | O | string |

##### Response
| property | type |
|---|---|
| sessionToken | string |

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

##### Response
| property | type |
|---|---|
| resultCode | int |


### app/updateUserInfo
사용자 정보 중 일부를 업데이트한다.

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |
| profileImageUrl | X | string |
| pushDuration | X | timestamp |
| lastLoginAlarmDuration | x | timestamp |

##### Response
| property | type |
|---|---|
| resultCode | int |

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
# Success
{
  "status": 200,
  "msg": "OK",
  "user": {
    "userName": "sjkim",
    "passwd": "010-1234-1214",
    "_id": "58ac500abf825f120f773d22",
    "phoneNumber": "010-1234-1214",
    "birthDay": 498841200
  }
}

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



## 유언 생성/삭제

### app/getTodaysQuestion

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |

##### Response
| property | NonOptional | type |
|----|----|----|
|question | O | [Question](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#question) |
|willItem | X | [WillItem](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#willitem) |

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

##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |
| questionID | O | string |
| answerText | X | string |
| answerPhoto | X | string |
| answerVideo | X | string |
| receivers | X | [[Receiver](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#receiver)] |
| lastUpdate | O | timestamp |

##### Response
| property | type |
|----|----|
| anwserID | string |


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

### getWIllItems
##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |

##### Response
| property | type |
|----|----|
| results | [[WillItem](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#willitem)] |

### getWIllItem
##### Request
| property | required | type |
|---|---|---|
| sessionToken | O | string |
| willItemID | O | string |

##### Response
| property | type |
|----|----|
| result | [WillItem](https://github.com/sicamp17-boramsangjo/server/blob/develop/README.md#willitem) |




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
