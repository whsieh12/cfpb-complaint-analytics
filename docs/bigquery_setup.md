# BigQuery setup (free sandbox, no credit card)

1. Prepare the file (renames the header only; no data row changes, row count is checked):

   ```
   python python/00_prepare_for_bigquery.py
   ```

   This writes `data/interim/complaints_bq.csv` (96,155 data rows).

2. Open https://console.cloud.google.com/bigquery, sign in, accept the terms, and create a project named
   `cfpb-complaint-analytics` (the sandbox needs no billing).

3. In the BigQuery Explorer: click the three dots next to the project, then **Create dataset**.
   Dataset ID `cfpb`, location **US**.

4. Click the three dots next to the `cfpb` dataset, then **Create table**:
   - Source: **Upload**, choose `data/interim/complaints_bq.csv`, format **CSV**
   - Table name: `raw_complaints`
   - Schema: turn on **Edit as text** and paste:

     ```
     date_received:STRING,product:STRING,sub_product:STRING,issue:STRING,sub_issue:STRING,company_public_response:STRING,company:STRING,state:STRING,zip_code:STRING,tags:STRING,submitted_via:STRING,date_sent_to_company:STRING,company_response_to_consumer:STRING,timely_response:STRING,complaint_id:STRING
     ```
   - Advanced options: **Header rows to skip** = `1`
   - Create table.

   Every column is loaded as text on purpose; dbt does the typing and cleaning.

5. Check the load (should return 96155, 96155):

   ```sql
   SELECT COUNT(*) AS rows_loaded,
          COUNT(DISTINCT complaint_id) AS distinct_ids,
          MIN(date_received) AS first_received,
          MAX(date_received) AS last_received
   FROM cfpb.raw_complaints;
   ```

Sandbox note: tables in the free sandbox expire after 60 days. The dbt code in this repo rebuilds everything.
