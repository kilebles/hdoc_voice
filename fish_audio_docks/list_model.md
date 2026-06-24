> ## Documentation Index
> Fetch the complete documentation index at: https://docs.fish.audio/llms.txt
> Use this file to discover all available pages before exploring further.

# List Models

> Get a list of all models



## OpenAPI

````yaml get /model
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
  /model:
    get:
      tags:
        - Model
      summary: List Models
      parameters:
        - in: query
          name: page_size
          description: Page size
          required: false
          schema:
            default: 10
            minimum: 1
            title: Page Size
            type: integer
          deprecated: false
        - in: query
          name: page_number
          description: Page number
          required: false
          schema:
            default: 1
            minimum: 1
            title: Page Number
            type: integer
          deprecated: false
        - in: query
          name: title
          description: Title to filter models
          required: false
          schema:
            anyOf:
              - type: string
              - type: 'null'
            default: null
            title: Title
          deprecated: false
        - in: query
          name: tag
          description: Tag to filter models
          required: false
          schema:
            anyOf:
              - items:
                  type: string
                type: array
              - type: string
              - type: 'null'
            default: null
            title: Tag
          deprecated: false
        - in: query
          name: self
          description: If True, only models created by the user will be returned
          required: false
          schema:
            default: false
            title: Self
            type: boolean
          deprecated: false
        - in: query
          name: author_id
          description: Author ID to filter models, this will be ignored if self is True
          required: false
          schema:
            anyOf:
              - type: string
              - type: 'null'
            default: null
            title: Author Id
          deprecated: false
        - in: query
          name: language
          description: Language to filter models
          required: false
          schema:
            anyOf:
              - items:
                  type: string
                type: array
              - type: string
              - type: 'null'
            default: null
            title: Language
          deprecated: false
        - in: query
          name: title_language
          description: Title language to filter models
          required: false
          schema:
            anyOf:
              - items:
                  type: string
                type: array
              - type: string
              - type: 'null'
            default: null
            title: Title Language
          deprecated: false
        - in: query
          name: sort_by
          description: ''
          required: false
          schema:
            default: score
            enum:
              - score
              - task_count
              - created_at
            title: Sort By
            type: string
          deprecated: false
      responses:
        '200':
          description: Request fulfilled, document follows
          headers: {}
          content:
            application/json:
              schema:
                properties:
                  total:
                    title: Total
                    type: integer
                  items:
                    items:
                      $ref: '#/components/schemas/ModelEntity'
                    title: Items
                    type: array
                  has_more:
                    anyOf:
                      - type: boolean
                      - type: 'null'
                    default: null
                    title: Has More
                required:
                  - total
                  - items
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
  schemas:
    ModelEntity:
      properties:
        _id:
          title: Id
          type: string
        type:
          enum:
            - svc
            - tts
          title: Type
          type: string
        title:
          title: Title
          type: string
        description:
          default: ''
          title: Description
          type: string
        cover_image:
          default: ''
          title: Cover Image
          type: string
        train_mode:
          default: full
          enum:
            - fast
            - full
          title: Train Mode
          type: string
        state:
          enum:
            - created
            - training
            - trained
            - failed
          title: State
          type: string
        tags:
          items:
            type: string
          title: Tags
          type: array
        samples:
          default: []
          items:
            $ref: '#/components/schemas/SampleEntity'
          title: Samples
          type: array
        created_at:
          format: date-time
          title: Created At
          type: string
        updated_at:
          format: date-time
          title: Updated At
          type: string
        languages:
          default: []
          items:
            type: string
          title: Languages
          type: array
        visibility:
          enum:
            - public
            - unlist
            - private
          title: Visibility
          type: string
        lock_visibility:
          default: false
          title: Lock Visibility
          type: boolean
        dmca_taken_down:
          anyOf:
            - type: boolean
            - type: 'null'
          default: false
          title: Dmca Taken Down
        default_text:
          default: ''
          title: Default Text
          type: string
        source:
          anyOf:
            - type: string
            - type: 'null'
          default: null
          title: Source
        quality:
          anyOf:
            - $ref: '#/components/schemas/ModelQualityEntity'
            - type: 'null'
          default: null
        like_count:
          title: Like Count
          type: integer
        mark_count:
          title: Mark Count
          type: integer
        shared_count:
          title: Shared Count
          type: integer
        task_count:
          title: Task Count
          type: integer
        unliked:
          default: false
          title: Unliked
          type: boolean
        liked:
          default: false
          title: Liked
          type: boolean
        marked:
          default: false
          title: Marked
          type: boolean
        author:
          $ref: '#/components/schemas/AuthorEntity'
      required:
        - _id
        - type
        - title
        - state
        - tags
        - created_at
        - updated_at
        - visibility
        - like_count
        - mark_count
        - shared_count
        - task_count
        - author
      title: ModelEntity
      type: object
    SampleEntity:
      properties:
        title:
          title: Title
          type: string
        text:
          title: Text
          type: string
        task_id:
          title: Task Id
          type: string
        audio:
          title: Audio
          type: string
      required:
        - title
        - text
        - task_id
        - audio
      title: SampleEntity
      type: object
    ModelQualityEntity:
      properties:
        audios:
          items:
            $ref: '#/components/schemas/ModelAudioQualityEntity'
          title: Audios
          type: array
        created_at:
          format: date-time
          title: Created At
          type: string
        updated_at:
          format: date-time
          title: Updated At
          type: string
      required:
        - created_at
        - updated_at
      title: ModelQualityEntity
      type: object
    AuthorEntity:
      properties:
        _id:
          title: Id
          type: string
        nickname:
          title: Nickname
          type: string
        avatar:
          title: Avatar
          type: string
      required:
        - _id
        - nickname
        - avatar
      title: AuthorEntity
      type: object
    ModelAudioQualityEntity:
      properties:
        filename:
          title: Filename
          type: string
        duration_ms:
          title: Duration Ms
          type: number
        language:
          default: unknown
          title: Language
          type: string
        quality:
          additionalProperties:
            type: number
          title: Quality
          type: object
        quality_passed:
          default: false
          title: Quality Passed
          type: boolean
        quality_reason:
          default: ''
          title: Quality Reason
          type: string
      required:
        - filename
        - duration_ms
      title: ModelAudioQualityEntity
      type: object
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer

````