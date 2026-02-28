# API 명세서 - 뚝딱레시피

Base URL: `https://api.ddukddak.app/v1`

## 공통

### 인증

Bearer 토큰 방식. `Authorization: Bearer <access_token>` 헤더 필수 (로그인/토큰 갱신 제외).

### 응답 형식

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

### 에러 응답

```json
{
  "success": false,
  "data": null,
  "error": "에러 메시지"
}
```

### HTTP 상태 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 201 | 생성 성공 |
| 400 | 잘못된 요청 |
| 401 | 인증 실패 (토큰 만료/누락) |
| 403 | 권한 없음 |
| 404 | 리소스 없음 |
| 429 | 요청 제한 초과 |
| 500 | 서버 내부 오류 |

---

## Auth

### POST /auth/login

소셜 로그인. 프로바이더별 토큰을 검증하고 JWT를 발급한다.

**Request**

```json
{
  "provider": "apple" | "google" | "kakao",
  "token": "소셜 프로바이더에서 발급한 ID 토큰"
}
```

**Response 200**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_abc123",
      "email": "user@example.com",
      "name": "홍길동",
      "avatarUrl": "https://...",
      "provider": "kakao",
      "createdAt": "2025-01-15T09:00:00Z"
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIs...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
    }
  }
}
```

**비고**
- 최초 로그인 시 자동 회원가입
- accessToken 만료: 1시간, refreshToken 만료: 30일
- iOS: Apple / Kakao / Google 지원
- Android: Kakao / Google 지원

---

### POST /auth/logout

로그아웃. 서버에서 리프레시 토큰을 무효화한다.

**Headers**: `Authorization: Bearer <access_token>`

**Response 200**

```json
{
  "success": true,
  "data": null
}
```

---

### POST /auth/refresh

만료된 액세스 토큰을 갱신한다.

**Request**

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 200**

```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**에러 401**: 리프레시 토큰 만료 시 재로그인 필요

---

### GET /auth/me

현재 로그인한 사용자 정보를 조회한다.

**Headers**: `Authorization: Bearer <access_token>`

**Response 200**

```json
{
  "success": true,
  "data": {
    "id": "user_abc123",
    "email": "user@example.com",
    "name": "홍길동",
    "avatarUrl": "https://...",
    "provider": "kakao",
    "createdAt": "2025-01-15T09:00:00Z"
  }
}
```

---

## Recipe

### POST /recipe/analyze

유튜브 URL을 받아 AI가 레시피를 분석한다.

**Headers**: `Authorization: Bearer <access_token>`

**Request**

```json
{
  "videoUrl": "https://www.youtube.com/watch?v=xxxxx"
}
```

**Response 200**

```json
{
  "success": true,
  "data": {
    "recipe": {
      "id": "recipe_abc123",
      "title": "김치찌개 만들기",
      "videoUrl": "https://www.youtube.com/watch?v=xxxxx",
      "thumbnailUrl": "https://img.youtube.com/vi/xxxxx/maxresdefault.jpg",
      "channelName": "백종원의 요리비책",
      "steps": [
        "김치를 한입 크기로 썬다",
        "돼지고기를 넣고 볶는다",
        "물을 넣고 끓인다",
        "두부를 넣고 5분 더 끓인다"
      ],
      "ingredients": [
        {
          "id": "ing_001",
          "name": "김치",
          "quantity": "300",
          "unit": "g",
          "price": 3000,
          "note": "묵은지 권장"
        },
        {
          "id": "ing_002",
          "name": "돼지고기 앞다리살",
          "quantity": "200",
          "unit": "g",
          "price": 4000
        },
        {
          "id": "ing_003",
          "name": "두부",
          "quantity": "1",
          "unit": "모",
          "price": 1500
        }
      ],
      "totalCost": 8500,
      "servings": 2,
      "userId": "user_abc123"
    },
    "analysisSteps": [
      { "label": "영상 정보 가져오는 중", "status": "completed" },
      { "label": "레시피 분석 중", "status": "completed" },
      { "label": "재료 가격 계산 중", "status": "completed" }
    ]
  }
}
```

**에러 400**: 유효하지 않은 유튜브 URL
**에러 429**: 분석 횟수 제한 초과 (무료 사용자: 하루 3회)

---

### POST /recipe/save

분석된 레시피를 컬렉션에 저장한다.

**Headers**: `Authorization: Bearer <access_token>`

**Request**

```json
{
  "id": "recipe_abc123",
  "title": "김치찌개 만들기",
  "videoUrl": "https://www.youtube.com/watch?v=xxxxx",
  "thumbnailUrl": "https://img.youtube.com/vi/xxxxx/maxresdefault.jpg",
  "channelName": "백종원의 요리비책",
  "steps": ["김치를 한입 크기로 썬다", "..."],
  "ingredients": [{ "id": "ing_001", "name": "김치", "quantity": "300", "unit": "g", "price": 3000 }],
  "totalCost": 8500,
  "servings": 2
}
```

**Response 201**

```json
{
  "success": true,
  "data": {
    "id": "recipe_abc123",
    "title": "김치찌개 만들기",
    "videoUrl": "https://www.youtube.com/watch?v=xxxxx",
    "thumbnailUrl": "https://img.youtube.com/vi/xxxxx/maxresdefault.jpg",
    "channelName": "백종원의 요리비책",
    "steps": ["김치를 한입 크기로 썬다", "..."],
    "ingredients": [{ "id": "ing_001", "name": "김치", "quantity": "300", "unit": "g", "price": 3000 }],
    "totalCost": 8500,
    "servings": 2,
    "savedAt": "2025-01-15T10:30:00Z",
    "userId": "user_abc123"
  }
}
```

---

### GET /recipe/list

사용자가 저장한 레시피 목록을 조회한다.

**Headers**: `Authorization: Bearer <access_token>`

**Response 200**

```json
{
  "success": true,
  "data": [
    {
      "id": "recipe_abc123",
      "title": "김치찌개 만들기",
      "videoUrl": "https://www.youtube.com/watch?v=xxxxx",
      "thumbnailUrl": "https://img.youtube.com/vi/xxxxx/maxresdefault.jpg",
      "channelName": "백종원의 요리비책",
      "steps": ["..."],
      "ingredients": [{ "..." }],
      "totalCost": 8500,
      "servings": 2,
      "savedAt": "2025-01-15T10:30:00Z",
      "userId": "user_abc123"
    }
  ]
}
```

---

### DELETE /recipe/{id}

저장된 레시피를 삭제한다.

**Headers**: `Authorization: Bearer <access_token>`

**Path Parameters**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| id | string | 레시피 ID |

**Response 200**

```json
{
  "success": true,
  "data": null
}
```

**에러 403**: 본인의 레시피가 아닌 경우
**에러 404**: 레시피를 찾을 수 없음

---

## Feed

### GET /feed

공개된 레시피 피드를 조회한다. 무한 스크롤을 지원한다.

**Headers**: `Authorization: Bearer <access_token>`

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| sort | string | `latest` | 정렬 기준 (`latest` / `popular`) |
| page | number | `1` | 페이지 번호 |
| limit | number | `20` | 페이지당 항목 수 (최대 50) |

**Response 200**

```json
{
  "success": true,
  "data": [
    {
      "id": "feed_abc123",
      "recipe": {
        "id": "recipe_abc123",
        "title": "김치찌개 만들기",
        "thumbnailUrl": "https://...",
        "channelName": "백종원의 요리비책",
        "totalCost": 8500,
        "servings": 2
      },
      "author": {
        "id": "user_abc123",
        "name": "홍길동",
        "avatarUrl": "https://..."
      },
      "likes": 42,
      "createdAt": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**비고**
- `latest`: 최신순 (createdAt 내림차순)
- `popular`: 인기순 (likes 내림차순)
- 다음 페이지 존재 여부: `data.length >= limit`이면 다음 페이지 있음

---

### GET /feed/{id}

피드 항목의 상세 정보를 조회한다. 전체 레시피 정보를 포함한다.

**Headers**: `Authorization: Bearer <access_token>`

**Path Parameters**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| id | string | 피드 항목 ID |

**Response 200**

```json
{
  "success": true,
  "data": {
    "id": "feed_abc123",
    "recipe": {
      "id": "recipe_abc123",
      "title": "김치찌개 만들기",
      "videoUrl": "https://www.youtube.com/watch?v=xxxxx",
      "thumbnailUrl": "https://...",
      "channelName": "백종원의 요리비책",
      "steps": [
        "김치를 한입 크기로 썬다",
        "돼지고기를 넣고 볶는다",
        "물을 넣고 끓인다",
        "두부를 넣고 5분 더 끓인다"
      ],
      "ingredients": [
        { "id": "ing_001", "name": "김치", "quantity": "300", "unit": "g", "price": 3000 }
      ],
      "totalCost": 8500,
      "servings": 2
    },
    "author": {
      "id": "user_abc123",
      "email": "user@example.com",
      "name": "홍길동",
      "avatarUrl": "https://...",
      "provider": "kakao",
      "createdAt": "2025-01-15T09:00:00Z"
    },
    "likes": 42,
    "createdAt": "2025-01-15T10:30:00Z"
  }
}
```

**에러 404**: 피드 항목을 찾을 수 없음

---

## 타입 정의

```typescript
interface User {
  id: string
  email: string
  name: string
  avatarUrl?: string
  provider: 'apple' | 'google' | 'kakao'
  createdAt: string
}

interface Recipe {
  id: string
  title: string
  videoUrl: string
  thumbnailUrl: string
  channelName: string
  steps: string[]
  ingredients: Ingredient[]
  totalCost: number
  servings: number
  savedAt?: string
  userId?: string
}

interface Ingredient {
  id: string
  name: string
  quantity: string
  unit: string
  price: number
  note?: string
}

interface FeedItem {
  id: string
  recipe: Recipe
  author: User
  likes: number
  createdAt: string
}

interface AuthTokens {
  accessToken: string
  refreshToken: string
}

interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}
```
