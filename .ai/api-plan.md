# REST API Plan for FashionDetector

## 1. Resources

| Resource | Description | Database Table(s) |
|----------|-------------|-------------------|
| Search | Represents a clothing search request including image upload | Connects to all analytics tables |
| Product | Represents search results from online stores | Not directly stored in DB |
| Analytics | Represents aggregated statistics about system usage | All materialized views |

## 2. Endpoints

### 2.1 Search Resource

#### 2.1.1 Initiate Search

- **Method**: POST
- **Path**: `/api/searches`
- **Description**: Upload an image and initiate a clothing search
- **Request**:
  - Content-Type: `multipart/form-data`
  - Body:
    ```json
    {
      "image": "[binary image data]",
      "stores": ["zalando", "modivo", "asos"] // Optional, defaults to all stores
    }
    ```
- **Response**:
  - Status: 202 Accepted
  - Body:
    ```json
    {
      "search_id": "string",
      "status": "processing",
      "estimated_time_seconds": 10,
      "timestamp": "2025-04-14T19:22:37Z"
    }
    ```
- **Error Codes**:
  - 400: Invalid image format (only JPEG/PNG accepted)
  - 413: Image too large
  - 429: Rate limit exceeded
  - 500: Server error

#### 2.1.2 Get Search Status

- **Method**: GET
- **Path**: `/api/searches/{search_id}`
- **Description**: Check the status of a previously initiated search
- **Parameters**:
  - `search_id` (path): Unique identifier for the search
- **Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "search_id": "string",
      "status": "processing|completed|failed",
      "elapsed_time_ms": 3500,
      "stores_searched": [
        {
          "name": "zalando",
          "status": "completed|processing|failed",
          "time_ms": 2800
        }
      ],
      "attributes_recognized": [
        {
          "name": "color",
          "value": "red",
          "confidence": 0.95
        }
      ],
      "result_count": 5,
      "timestamp": "2025-04-14T19:22:37Z"
    }
    ```
- **Error Codes**:
  - 404: Search not found
  - 500: Server error

### 2.2 Product Resource

#### 2.2.1 Get Search Results

- **Method**: GET
- **Path**: `/api/searches/{search_id}/products`
- **Description**: Retrieve the results of a completed search
- **Parameters**:
  - `search_id` (path): Unique identifier for the search
- **Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "search_id": "string",
      "products": [
        {
          "title": "string",
          "store": "string",
          "url": "string", 
          "similarity_score": 0.92,
          "attributes": {
            "color": "red",
            "pattern": "striped",
            "cut": "slim",
            "brand": "brand_name"
          },
          "alternatives": [
            {
              "color": "blue",
              "url": "string"
            }
          ]
        }
      ],
      "total_results_found": 5,
      "total_time_ms": 8500
    }
    ```
- **Error Codes**:
  - 404: Search not found
  - 409: Search still in progress
  - 500: Server error

### 2.3 Analytics Resource (Admin/Service Access Only)

#### 2.3.1 Get Attribute Statistics

- **Method**: GET
- **Path**: `/api/analytics/attributes`
- **Description**: Retrieve statistics about recognized clothing attributes
- **Parameters**:
  - `start_date` (query): Filter by start date (ISO format)
  - `end_date` (query): Filter by end date (ISO format)
  - `attribute_name` (query): Filter by attribute name (color, pattern, cut, brand)
- **Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "data": [
        {
          "attribute_name": "color",
          "attribute_value": "red",
          "recognition_count": 156,
          "avg_recognition_time_ms": 320,
          "day": "2025-04-14"
        }
      ],
      "total_count": 1
    }
    ```
- **Error Codes**:
  - 400: Invalid parameters
  - 401: Unauthorized
  - 403: Forbidden
  - 500: Server error

#### 2.3.2 Get Store Statistics

- **Method**: GET
- **Path**: `/api/analytics/stores`
- **Description**: Retrieve statistics about store searches
- **Parameters**:
  - `start_date` (query): Filter by start date (ISO format)
  - `end_date` (query): Filter by end date (ISO format)
  - `store_name` (query): Filter by store name
- **Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "data": [
        {
          "store_name": "zalando",
          "search_count": 324,
          "successful_search_count": 312,
          "avg_response_time_ms": 2850,
          "day": "2025-04-14"
        }
      ],
      "total_count": 1
    }
    ```
- **Error Codes**:
  - 400: Invalid parameters
  - 401: Unauthorized
  - 403: Forbidden
  - 500: Server error

#### 2.3.3 Get Performance Statistics

- **Method**: GET
- **Path**: `/api/analytics/performance`
- **Description**: Retrieve overall search performance metrics
- **Parameters**:
  - `start_date` (query): Filter by start date (ISO format)
  - `end_date` (query): Filter by end date (ISO format)
- **Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "data": [
        {
          "day": "2025-04-14",
          "search_count": 128,
          "avg_total_time_ms": 7850,
          "max_total_time_ms": 12300,
          "avg_analysis_time_ms": 4200,
          "avg_search_time_ms": 3650,
          "avg_result_count": 4.2,
          "successful_search_count": 115
        }
      ],
      "total_count": 1
    }
    ```
- **Error Codes**:
  - 400: Invalid parameters
  - 401: Unauthorized
  - 403: Forbidden
  - 500: Server error

## 3. Authentication and Authorization

### 3.1 Authentication

Authentication is implemented via JSON Web Tokens (JWT) provided by Supabase:

- **Public API**: Search and Product endpoints are publicly accessible
- **Analytics API**: Restricted to admin users and service roles
- **Token Management**: Handled by Supabase authentication

### 3.2 Authorization

Authorization is implemented through Supabase RLS and API service logic:

- **Public Access**: Anonymous users can submit searches and retrieve results
- **Service Role**: Required for internal operations (data collection, metrics)
- **Admin Access**: Required for analytics endpoints

## 4. Validation and Business Logic

### 4.1 Search Request Validation

- Image format must be JPEG or PNG
- Image size must not exceed 10 MB
- Store names (if provided) must be from the supported list

### 4.2 Key Business Logic

#### 4.2.1 Image Analysis Logic

- Extract garment attributes using AI model
- Identify key characteristics: color, pattern, cut, brand
- Generate structured attribute data for search
- Record attribute recognition metrics

#### 4.2.2 Search Logic

- Execute parallel searches in specified online stores
- Apply 85% similarity threshold for matches
- Return maximum 5 products prioritized by match quality
- Include alternative colors when exact match is unavailable
- Track store search performance

#### 4.2.3 Performance Monitoring

- Track total search time (target: under 10 seconds)
- Track image analysis time
- Track store search time
- Record metrics for analytics and optimization

### 4.3 Error Handling

- Graceful timeout handling for searches exceeding 10 seconds
- Fallback mechanisms for store search failures
- Comprehensive error logging for troubleshooting

## 5. Implementation Notes

### 5.1 FastAPI Implementation

The API will be implemented using FastAPI, which provides:

- Automatic OpenAPI documentation
- Request validation
- Asynchronous request handling
- WebSocket support for real-time status updates

### 5.2 Background Tasks

Long-running operations will be handled using FastAPI background tasks:

- Image analysis
- Store searches
- Metrics collection and aggregation

### 5.3 Caching Strategy

- Cache frequently recognized attributes
- Cache store search results temporarily
- Use Redis for distributed caching

### 5.4 Rate Limiting

- 10 searches per hour for anonymous users
- 100 searches per hour for authenticated users
- Configurable limits for premium users in future versions 