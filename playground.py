import os

from dotenv import load_dotenv
from openai import OpenAI
from vanna.chromadb import ChromaDB_VectorStore
from vanna.openai import OpenAI_Chat
from vanna.types import TrainingPlan

load_dotenv()

# 1. Setup DeepSeek with Vanna
deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", ""), base_url="https://api.deepseek.com"
)


class VannaDeepSeek(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, client=deepseek_client, config=config)


vn = VannaDeepSeek(config={"model": "deepseek-chat"})

# 2. Connect to database
vn.connect_to_postgres(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", 5432)),
    dbname=os.getenv("POSTGRES_DB", "postgres"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
)

# 3. Train with your table structure
vn.train(
    documentation="""
### Database Structure:

**Tables:**
1. **main_tenant**
                          Table "public.main_tenant"
      Column       |           Type           | Collation | Nullable | Default
-------------------+--------------------------+-----------+----------+---------
 id                | uuid                     |           | not null |
 additional_info   | jsonb                    |           |          |
 address           | character varying        |           |          |
 address2          | character varying        |           |          |
 city              | character varying(255)   |           |          |
 country           | character varying(255)   |           |          |
 email             | character varying(255)   |           |          |
 phone             | character varying(255)   |           |          |
 region            | character varying(255)   |           |          |
 state             | character varying(255)   |           |          |
 title             | character varying(255)   |           |          |
 zip               | character varying(255)   |           |          |
 tenant_profile_id | uuid                     |           | not null |
 created_by_id     | uuid                     |           |          |
 updated_at        | timestamp with time zone |           |          |
 updated_by_id     | uuid                     |           |          |
 created_at        | timestamp with time zone |           |          |
Indexes:
    "main_tenant_pkey" PRIMARY KEY, btree (id)
    "main_tenant_created_by_id_064208db" btree (created_by_id)
    "main_tenant_tenant_profile_id_788aa968" btree (tenant_profile_id)
    "main_tenant_updated_by_id_51ac04a7" btree (updated_by_id)
Foreign-key constraints:
    "main_tenant_created_by_id_064208db_fk_users_users_id" FOREIGN KEY (created_by_id) REFERENCES users_users(id) DEFERRABLE INITIALLY DEFERRED
    "main_tenant_tenant_profile_id_788aa968_fk_main_tena" FOREIGN KEY (tenant_profile_id) REFERENCES main_tenant_profile(id) DEFERRABLE INITIALLY DEFERRED
    "main_tenant_updated_by_id_51ac04a7_fk_users_users_id" FOREIGN KEY (updated_by_id) REFERENCES users_users(id) DEFERRABLE INITIALLY DEFERRED

   **Sample Data**:
                  id                  |  title  |          tenant_profile_id           | updated_by_id |          updated_at           | created_by_id |          created_at           | zip | state | address | address2 | city | country | email | phone | region |                                                                                                                                                                                                                                             additional_info                                                                                                                                                                                                                                              
--------------------------------------+---------+--------------------------------------+---------------+-------------------------------+---------------+-------------------------------+-----+-------+---------+----------+------+---------+-------+-------+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 32daa3c9-d41e-4019-bd71-8a7ce0825d1d | Nines   | b68dacbf-6b34-433e-9b4b-f9a0ebc8458b |               | 2025-08-29 17:57:27.660551+02 |               | 2025-08-29 17:57:27.660498+02 |     |       |         |          |      |         |       |       |        | 
 ea776673-3987-429f-b969-e9afb606dc8c | Abacus  | b68dacbf-6b34-433e-9b4b-f9a0ebc8458b |               | 2025-08-29 14:18:52.503408+02 |               | 2025-06-17 07:04:13.007+02    |     |       |         |          |      |         |       |       |        | 
 81ba1022-b08c-4eb7-af2d-307edbc8c2d4 | Default | b68dacbf-6b34-433e-9b4b-f9a0ebc8458b |               | 2025-08-29 14:18:52.503408+02 |               | 2025-02-19 15:32:59+02        |     |       |         |          |      |         |       |       |        | {"general_settings": {"lang": "en", "laundry": false, "timezone": 0, "door_lock": {"kaba": false, "ving_card": false}, "vip_status": false, "visionline": false, "aggregate_db": false, "aperio_locks": false, "check_in_out": false, "auto_checkout": false, "main_dashboard": "d7e06291-5f35-4a41-88b7-703a1201f532", "roomio_node_url": "https://nodered.grms.room.io/", "controllers_sync": false, "opera_integration": false, "visionline_card_system": false, "suite_rooms_controls_sync": false}}

2. **main_room**
                         Table "public.main_room"
     Column      |          Type          | Collation | Nullable | Default
-----------------+------------------------+-----------+----------+---------
 id              | uuid                   |           | not null |
 created_at      | bigint                 |           |          |
 updated_at      | bigint                 |           |          |
 number          | character varying(100) |           | not null |
 floor           | character varying(255) |           | not null |
 block           | character varying(255) |           | not null |
 active          | boolean                |           | not null |
 state           | smallint[]             |           | not null |
 public_area_id  | integer                |           |          |
 pan_id          | character varying(255) |           |          |
 building        | character varying(255) |           |          |
 door_lock_id    | character varying(255) |           |          |
 suite_id        | uuid                   |           |          |
 tenant_id       | uuid                   |           | not null |
 updated_by_id   | uuid                   |           |          |
 type_id         | uuid                   |           |          |
 status          | character varying(255) |           | not null |
 created_by_id   | uuid                   |           |          |
 additional_info | jsonb                  |           |          |
 label           | character varying(255) |           |          |
Indexes:
    "main_room_pkey" PRIMARY KEY, btree (id)
    "main_room_created_by_id_68d4dabf" btree (created_by_id)
    "main_room_door_lock_id_62d7d532_like" btree (door_lock_id varchar_pattern_ops)
    "main_room_door_lock_id_key" UNIQUE CONSTRAINT, btree (door_lock_id)
    "main_room_suite_id_e8079be7" btree (suite_id)
    "main_room_tenant_id_493b6a4b" btree (tenant_id)
    "main_room_type_id_169c6da8" btree (type_id)
    "main_room_updated_by_id_1bc80525" btree (updated_by_id)
    "unique_active_room" UNIQUE, btree (number, floor, block, tenant_id) WHERE active
Foreign-key constraints:
    "main_room_created_by_id_68d4dabf_fk_users_users_id" FOREIGN KEY (created_by_id) REFERENCES users_users(id) DEFERRABLE INITIALLY DEFERRED
    "main_room_suite_id_e8079be7_fk_main_room_id" FOREIGN KEY (suite_id) REFERENCES main_room(id) DEFERRABLE INITIALLY DEFERRED
    "main_room_tenant_id_493b6a4b_fk_main_tenant_id" FOREIGN KEY (tenant_id) REFERENCES main_tenant(id) DEFERRABLE INITIALLY DEFERRED
    "main_room_type_id_169c6da8_fk_main_room_type_id" FOREIGN KEY (type_id) REFERENCES main_room_type(id) DEFERRABLE INITIALLY DEFERRED
    "main_room_updated_by_id_1bc80525_fk_users_users_id" FOREIGN KEY (updated_by_id) REFERENCES users_users(id) DEFERRABLE INITIALLY DEFERRED

   **Sample Data**:
                  id                  |  created_at   |  updated_at   | number | floor | block | active | state | public_area_id | pan_id | building | door_lock_id | suite_id |              tenant_id               |            updated_by_id             |               type_id                | status | created_by_id | additional_info | label 
--------------------------------------+---------------+---------------+--------+-------+-------+--------+-------+----------------+--------+----------+--------------+----------+--------------------------------------+--------------------------------------+--------------------------------------+--------+---------------+-----------------+-------
 5382a389-e0f3-4c7a-9645-3d4a868cd969 | 1750138740471 | 1750138740484 | 242    | 2     | A     | t      | {1}   |                |        |          |              |          | ea776673-3987-429f-b969-e9afb606dc8c |                                      | 1e2b0617-1a8a-4c7d-b353-b28d1fab7caf | OFF    |               |                 | 
 b53ff5a0-0baf-4e21-8b6a-8a0154e555f9 |    1741859500 | 1741932076768 | 12     | 1     | A     | t      | {0}   |                |        |          |              |          | 81ba1022-b08c-4eb7-af2d-307edbc8c2d4 |                                      | 6005d07b-224d-4ad8-b540-4b35257a377c | OFF    |               |                 | 
 e68f8518-5cf0-4465-8b7c-b0c4413c0677 | 1750138741562 | 1750138741586 | 243    | 2     | A     | t      | {1}   |                |        |          |              |          | ea776673-3987-429f-b969-e9afb606dc8c |                                      | 5d5ccca9-1c41-4b0a-9f9c-4ce9898b34f2 | OFF    |               |                 | 
 236b2128-28f2-468b-83c0-62dc66a6ea63 | 1750138728724 | 1750138728736 | 138    | 1     | A     | t      | {1}   |                |        |          |              |          | ea776673-3987-429f-b969-e9afb606dc8c |                                      | 5d5ccca9-1c41-4b0a-9f9c-4ce9898b34f2 | OFF    |               |                 | 

3. **main_device**
                         Table "public.main_device"
      Column       |          Type          | Collation | Nullable | Default
-------------------+------------------------+-----------+----------+---------
 id                | uuid                   |           | not null |
 created_at        | bigint                 |           |          |
 name              | character varying(255) |           | not null |
 type              | character varying(255) |           | not null |
 status            | boolean                |           | not null |
 label             | character varying(255) |           |          |
 additional_info   | jsonb                  |           |          |
 device_data       | jsonb                  |           |          |
 external_id       | character varying(255) |           |          |
 customer_id       | uuid                   |           |          |
 tenant_id         | uuid                   |           | not null |
 device_profile_id | uuid                   |           | not null |
 room_id           | uuid                   |           |          |
 is_active         | boolean                |           | not null |
 card_id           | uuid                   |           |          |
 created_by_id     | uuid                   |           |          |
Indexes:
    "main_device_pkey" PRIMARY KEY, btree (id)
    "main_device_card_id_1b1fa407" btree (card_id)
    "main_device_created_by_id_cabf8fbb" btree (created_by_id)
    "main_device_customer_id_f46b1c00" btree (customer_id)
    "main_device_device_profile_id_c014bb62" btree (device_profile_id)
    "main_device_room_id_03a557be" btree (room_id)
    "main_device_tenant_id_d3066abc" btree (tenant_id)
    "unique_device_name_tenant_is_active" UNIQUE, btree (lower(name::text), tenant_id) WHERE is_active
Foreign-key constraints:
    "main_device_card_id_1b1fa407_fk_access_manager_cards_id" FOREIGN KEY (card_id) REFERENCES access_manager_cards(id) DEFERRABLE INITIALLY DEFERRED
    "main_device_created_by_id_cabf8fbb_fk_users_users_id" FOREIGN KEY (created_by_id) REFERENCES users_users(id) DEFERRABLE INITIALLY DEFERRED
    "main_device_customer_id_f46b1c00_fk_main_customer_id" FOREIGN KEY (customer_id) REFERENCES main_customer(id) DEFERRABLE INITIALLY DEFERRED
    "main_device_device_profile_id_c014bb62_fk_main_devi" FOREIGN KEY (device_profile_id) REFERENCES main_device_profile(id) DEFERRABLE INITIALLY DEFERRED
    "main_device_room_id_03a557be_fk_main_room_id" FOREIGN KEY (room_id) REFERENCES main_room(id) DEFERRABLE INITIALLY DEFERRED
    "main_device_tenant_id_d3066abc_fk_main_tenant_id" FOREIGN KEY (tenant_id) REFERENCES main_tenant(id) DEFERRABLE INITIALLY DEFERRED

  **Sample Data**

                  id                  |  created_at   |            name             |  type   | status | label |                      additional_info                       | device_data | external_id | customer_id |              tenant_id               |          device_profile_id           |               room_id                | is_active | card_id | created_by_id 
--------------------------------------+---------------+-----------------------------+---------+--------+-------+------------------------------------------------------------+-------------+-------------+-------------+--------------------------------------+--------------------------------------+--------------------------------------+-----------+---------+---------------
 4a6f5263-a4ea-4ef0-aa01-1585b8597dcc |    1741858784 | YanisTestDevice2            | default | f      |       |                                                            |             |             |             | 81ba1022-b08c-4eb7-af2d-307edbc8c2d4 | 857a9e59-1f87-4f09-9485-5b5b343ce1ec | b53ff5a0-0baf-4e21-8b6a-8a0154e555f9 | f         |         | 
 7cf4c87a-2453-46ed-b2a4-7334c16ada6e | 1747894453788 | 70:2a:e7:45:85:70           | default | f      |       |                                                            |             |             |             | b9d765ea-8f4d-474f-ad0f-d0b9a2cc864b | 1f0ba8ab-bd12-490c-8e05-5c93baa2a4eb |                                      | f         |         | 
 9e0cf418-fc3e-4431-929e-5e4f67f64cc9 | 1746440264773 | HRC350_tk163ukWdK           | default | f      |       |                                                            |             |             |             | 19db6caf-0607-44eb-baf5-157b4cdd555b | 11a1d768-9586-4203-bef9-57313db978cd |                                      | t         |         | 
 d795226c-d55d-40eb-9955-362b1bf4a1cc |    1740050394 | bc:e3:5c:0e:d3:e4           | default | f      |       |                                                            |             |             |             | 81ba1022-b08c-4eb7-af2d-307edbc8c2d4 | 857a9e59-1f87-4f09-9485-5b5b343ce1ec |                                      | t         |         | 
 bfbcf140-4698-4a58-be72-a18c0f8132c5 |    1740050394 | 24:3e:b2:da:d3:e3           | default | f      |       |                                                            |             |             |             | 81ba1022-b08c-4eb7-af2d-307edbc8c2d4 | 857a9e59-1f87-4f09-9485-5b5b343ce1ec |                                      | t         |         | 
 0be60f9e-d15e-4c0a-abb0-28bad4a19f29 | 1747808058962 | RoomIo                      | default | f      |       | {"gateway": true, "description": "", "roomio_node": false} |             |             |             | b9d765ea-8f4d-474f-ad0f-d0b9a2cc864b | 1f0ba8ab-bd12-490c-8e05-5c93baa2a4eb |                                      | t         |         | 

4. **shuttle_ts_kv_dictionary**
                          Table "public.shuttle_ts_kv_dictionary"
 Column |          Type          | Collation | Nullable |             Default
--------+------------------------+-----------+----------+----------------------------------
 key    | character varying(255) |           | not null |
 key_id | integer                |           | not null | generated by default as identity
Indexes:
    "shuttle_ts_kv_dictionary_pkey" PRIMARY KEY, btree (key_id)
    "shuttle_ts_kv_dictionary_key_key_id_6c61c716_uniq" UNIQUE CONSTRAINT, btree (key, key_id)

  **Sample Data**
            key             | key_id 
----------------------------+--------
 service_ERRORS_COUNT       |      1
 ALL_ERRORS_COUNT           |      2
 receivedBytesFromDevices   |      3
 convertedBytesFromDevice   |      4
 allReceivedBytesFromTB     |      5
 allBytesSentToTB           |      6
 allBytesSentToDevices      |      7
 eventsProduced             |      8
 eventsSent                 |      9

5. **shuttle_ts_kv**
                     Table "public.shuttle_ts_kv"
  Column   |           Type           | Collation | Nullable | Default
-----------+--------------------------+-----------+----------+---------
 ts        | timestamp with time zone |           | not null |
 key       | integer                  |           | not null |
 bool_v    | boolean                  |           |          |
 str_v     | text                     |           |          |
 long_v    | bigint                   |           |          |
 dbl_v     | double precision         |           |          |
 json_v    | jsonb                    |           |          |
 entity_id | uuid                     |           | not null |
Indexes:
    "shuttle_ts_kv_entity_id_ts_idx" btree (entity_id, ts DESC)
    "shuttle_ts_kv_key_ts_idx" btree (key, ts DESC)
    "shuttle_ts_kv_ts_idx" btree (ts DESC)
Triggers:
    ts_insert_blocker BEFORE INSERT ON shuttle_ts_kv FOR EACH ROW EXECUTE FUNCTION _timescaledb_functions.insert_blocker()

  **Sample Data**

             ts             | key | bool_v | str_v |  long_v   | dbl_v | json_v |              entity_id               
----------------------------+-----+--------+-------+-----------+-------+--------+--------------------------------------
 2025-06-10 02:00:22.599+02 | 135 |        |       |         1 |       |        | 0f36c847-47a8-47d2-9b25-5ba9e5c94a26
 2025-06-10 02:00:28.942+02 |  51 |        |       |         0 |       |        | 31c7f9e8-621a-4d1b-8d6d-eaa0920394b8
 2025-06-10 02:00:28.942+02 |  52 |        |       |         0 |       |        | 31c7f9e8-621a-4d1b-8d6d-eaa0920394b8
 2025-06-10 02:00:28.942+02 |  53 |        |       |         0 |       |        | 31c7f9e8-621a-4d1b-8d6d-eaa0920394b8
 2025-06-10 02:00:28.942+02 |  54 |        |       |         0 |       |        | 31c7f9e8-621a-4d1b-8d6d-eaa0920394b8
 2025-06-10 02:00:28.942+02 |  55 |        |       |         1 |       |        | 31c7f9e8-621a-4d1b-8d6d-eaa0920394b8
 2025-06-10 02:00:28.942+02 |  12 |        |       |           |    22 |        | 31c7f9e8-621a-4d1b-8d6d-eaa0920394b8
 2025-06-10 02:00:28.942+02 |  10 |        |       |         0 |       |        | 31c7f9e8-621a-4d1b-8d6d-eaa0920394b8
 2025-06-10 02:00:28.942+02 |  11 |        |       |         0 |       |        | 31c7f9e8-621a-4d1b-8d6d-eaa0920394b8
 2025-06-10 02:00:22.684+02 |  13 |        |       |           |    22 |        | 84aa8f18-57f9-4a60-9f32-835cc2df3db7
 2025-06-10 02:00:22.684+02 | 136 |        |       |         3 |       |        | 84aa8f18-57f9-4a60-9f32-835cc2df3db7
 2025-06-10 02:00:22.684+02 |  12 |        |       |           |    22 |        | 84aa8f18-57f9-4a60-9f32-835cc2df3db7
 2025-06-10 02:01:12.322+02 |  12 |        |       |           |  19.2 |        | 834099c8-8f19-4545-9413-d24e45c788da



### Key Points:
- **Relationships**: One-to-many between `main_tenant` and 'main_room', 'main_device'.
- **Relationships**: One-to-many between `main_room` and `main_device`.
- **Relationships**: One-to-many between `main_device` and `shuttle_ts_kv`. Fields `main_device`.`id` and `shuttle_ts_kv`.`entity_id`
- **Relationships**: One-to-many between `shuttle_ts_kv` and `shuttle_ts_kv_dictionary`. Fields `shuttle_ts_kv`.`key` and `shuttle_ts_kv_dictionary`.`key_id`

### Example Query:
- **Show me the average Room Temperature for the period 2025-06-18 - 2025-08-08 in 143 rooms in Abacus tenant.**:
   ```sql
    SELECT AVG(tk.dbl_v)
    FROM shuttle_ts_kv AS tk
    INNER JOIN main_device AS md ON tk.entity_id = md.id
    INNER JOIN main_room AS mr ON md.room_id = mr.id
    INNER JOIN main_tenant AS mt ON mr.tenant_id = mt.id
    WHERE tk.ts BETWEEN '2025-06-18' AND '2025-08-08' AND tk.key = (
        SELECT tkd.key_id FROM shuttle_ts_kv_dictionary as tkd
        WHERE tkd.key = 'Room Temperature') AND mt.title = 'Abacus' AND mr.id IN (
        SELECT smr.id FROM main_room AS smr
        WHERE smr.number = '143' AND md.tenant_id = (
            SELECT ssmt.id FROM main_tenant AS ssmt
            WHERE ssmt.title = 'Abacus'
        ) LIMIT 143
    )
    ```
    """
)
vn.train(
    documentation="When user asks for value from shuttle_ts_kv, give first non-null value from columns `bool_v, str_v, long_v, dbl_v, json_v `."
)

# 1. Get tenant from request params
# 2. Get to AI file structure of DB
# 3. WebUI Vanna.AI

# - Написать у нас данные записивается по изменению

# 4. Ask questions in natural language
# question = "Show me the last 20 rows of shuttle_ts_kv where entity_id is c2641994-1723-4cdd-bc62-f4328752acee"
question = "Show me the average Room Temperature for the last 7 days in 143 rooms in Abacus tenant."
# question = "Show me the last value of SETPOINT for in 138 rooms in Abacus tenant."
sql = vn.generate_sql(question)
print(f"Question: {question}")
print(f"Generated SQL: {sql}")

# 5. Execute and see results
results = vn.run_sql(sql)
print(f"Results: {results}")
with open(f"{question}_result.log", "w") as f:
    f.write(str(results))
