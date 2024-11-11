---
hide:
  - footer
---

# Parsers

## Swagger

  file example
  
  parsed object


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