> ## Documentation Index
> Fetch the complete documentation index at: https://docs.fish.audio/llms.txt
> Use this file to discover all available pages before exploring further.

# Delete Model

> Delete an existing model



## OpenAPI

````yaml delete /model/{id}
openapi: 3.1.0
info:
  title: FishAudio OpenAPI
  version: '1'
servers:
  - description: Fish Audio API
    url: https://api.fish.audio
security: []
tags: []
paths:
  /model/{id}:
    delete:
      tags:
        - Model
      summary: Delete Model
      parameters:
        - in: path
          name: id
          description: ''
          required: true
          schema:
            title: Id
            type: string
          deprecated: false
      responses:
        '200':
          description: Request fulfilled, document follows
          headers: {}
        '401':
          description: No permission -- see authorization schemes
          headers: {}
          content:
            application/json:
              schema:
                properties:
                  status:
                    title: Status
                    type: integer
                  message:
                    title: Message
                    type: string
                required:
                  - status
                  - message
                type: object
        '422':
          description: ''
          headers: {}
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    loc:
                      title: Location
                      description: error field
                      type: array
                      items:
                        type: string
                    type:
                      title: Type
                      description: error type
                      type: string
                    msg:
                      title: Message
                      description: error message
                      type: string
                    ctx:
                      title: Context
                      description: error context
                      type: string
                    in:
                      title: In
                      type: string
                      enum:
                        - path
                        - query
                        - header
                        - cookie
                        - body
                  required:
                    - loc
                    - type
                    - msg
      security:
        - BearerAuth: []
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer

````