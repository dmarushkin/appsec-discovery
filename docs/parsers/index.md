---
hide:
  - footer
---

# Parsers

## Swagger

Swagger file:

```
openapi: 3.0.3
info:
  title: Swagger Petstore - OpenAPI 3.0
  ...
paths:
  /user/login:
    get:
      tags:
        - user
      summary: Logs user into the system
      description: ''
      operationId: loginUser
      parameters:
        - name: username
          in: query
          description: The user name for login
          required: false
          schema:
            type: string
        - name: password
          in: query
          description: The password for login in clear text
          required: false
          schema:
            type: string
      responses:
        '200':
          description: successful operation
          headers:
            X-Rate-Limit:
              description: calls per hour allowed by the user
              schema:
                type: integer
                format: int32
            X-Expires-After:
              description: date in UTC when token expires
              schema:
                type: string
                format: date-time
          content:
            application/xml:
              schema:
                type: string
            application/json:
              schema:
                type: string
        '400':
          description: Invalid username/password supplied

```
  
Scanned structure:

```
appsec-discovery --source tests/swagger_samples

- hash: 40140abef3b5f45d447d16e7180cc231
  object_name: Route /user/login (GET)
  object_type: route
  parser: swagger
  severity: high
  tags:
  - auth
  file: swagger.yaml
  line: 1
  properties:
    path:
      prop_name: path
      prop_value: /user/login
      severity: medium
      tags:
      - auth
    method:
      prop_name: method
      prop_value: GET
  fields:
    query.param.username:
      field_name: query.param.username
      field_type: string
      file: swagger.yaml
      line: 1
      severity: medium
      tags:
      - auth
    query.param.password:
      field_name: query.param.password
      field_type: string
      file: swagger.yaml
      line: 1
      severity: high
      tags:
      - auth
    output:
      field_name: output
      field_type: string
      file: swagger.yaml
      line: 1

```


## Protobuf

Proto file:

```
syntax = "proto3";

package com.surajgharat.practice.grpc.service;

service SumService {
  rpc Sum(SumInput) returns (SumOutput) {}
}

message SumInput {
  int32 n1 = 1;
  int32 n2 = 2;
}

message SumOutput { int32 result = 1; }
```

Scanned structure:
  
```
appsec-discovery --source tests/protobuf_samples/

- hash: 9e167a92c3a4ecb34a52a148775b3dba
  object_name: Rpc /com.surajgharat.practice.grpc.service.SumService/Sum
  object_type: rpc
  parser: protobuf
  file: test2.proto
  line: 1
  properties: {}
  fields:
    input.SumInput.n1:
      field_name: SumInput.n1
      field_type: int32
      file: test2.proto
      line: 1
    input.SumInput.n2:
      field_name: SumInput.n2
      field_type: int32
      file: test2.proto
      line: 2
    output.SumOutput.result:
      field_name: SumOutput.result
      field_type: int32
      file: test2.proto
      line: 1
```


## Graphql

Graphql file:

```
type MgmQueries

extend type Query {
    mgm: MgmQueries!
}

extend type MgmQueries  {
    offer(input: MgmOfferInput!): MgmOfferPayload! 
    promoterInfo(input: MgmPromoterInfoInput!): MgmPromoterInfoPayload! 
}

input MgmOfferInput {
    link: String!
}

input MgmPromoterInfoInput {
    link: String!
}

type MgmPromoterInfoPayload {
    firstName: String!
    lastName: String!
}

type MgmOfferPayload {
    offer: MgmOffer!
}
```
  
Scanned structure:

```
appsec-discovery --source tests/graphql_samples/

- hash: 073e49453527d0792215a5359bf237db
  object_name: Query MgmQueries.offer
  object_type: query
  parser: graphql
  file: query.graphql
  line: 91
  properties: {}
  fields:
    input.MgmOfferInput.link:
      field_name: input.MgmOfferInput.link
      field_type: String
      file: query.graphql
      line: 241
    output.MgmOfferPayload.offer:
      field_name: output.MgmOfferPayload.offer
      field_type: MgmOffer
      file: query.graphql
      line: 413
- hash: 8a878eb2050c855faab96d2e52cc7cf8
  object_name: Query MgmQueries.promoterInfo
  object_type: query
  parser: graphql
  severity: high
  tags:
  - pii
  file: query.graphql
  line: 143
  properties: {}
  fields:
    input.MgmPromoterInfoInput.link:
      field_name: input.MgmPromoterInfoInput.link
      field_type: String
      file: query.graphql
      line: 291
    output.MgmPromoterInfoPayload.firstName:
      field_name: output.MgmPromoterInfoPayload.firstName
      field_type: String
      file: query.graphql
      line: 342
      severity: high
      tags:
      - pii
    output.MgmPromoterInfoPayload.lastName:
      field_name: output.MgmPromoterInfoPayload.lastName
      field_type: String
      file: query.graphql
      line: 365
      severity: high
      tags:
      - pii
```

## Sql migrations

  file example
  
  parsed object