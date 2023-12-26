## Schema Overview

### Models

`user`

- id [int] (primary key)
- email [string]
- password [string]
- experience [int]

`user_list_book`

- id [int] (primary key)
- listId [int] (foreign key)
- bookID [string] (foreign key)
- isbn [string]

`user_list`

- id [int] (primary key)
- userId [int] (foreign key)
- name [string]

`progress_entry`

- id [int] (primary key)
- userId [int] (foreign key)
- bookId [string] (foreign key)
- currentPage [int]
- totalPages [int]

`experience_entry`

- id [int] (primary key)
- userId [int] (foreign key)
- experience [int]
- reason [string] (enum) 50% read, 100% read, etc.
