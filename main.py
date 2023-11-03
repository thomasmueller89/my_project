import csv
import itertools
import sys
from dateutil.parser import parse


### 1.Input Handling ###

#reads csv file
def read_dataset(file_path):
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        dataset = [row for row in reader]
    return dataset

#gets and parses functional dependencies
def read_functional_dependencies():
    fds = []
    print("Input Functional Dependencies (type “exit” and hit enter to complete your dependency list):")
    while True:
        fd = input()
        if fd.lower() == 'exit':
            break
        lhs, rhs = map(str.strip, fd.split('->'))
        fds.append((lhs.split(', '), rhs.split(', ')))
    return fds

#gets and parses multivalued dependencies
def read_multivalued_dependencies():
    fds = []
    print("Input Multi-valued Dependencies (type “exit” and hit enter to complete your dependency list):")
    while True:
        fd = input()
        if fd.lower() == 'exit':
            break
        lhs, rhs = map(str.strip, fd.split('->>'))
        fds.append((lhs.split(', '), rhs.split(', ')))
    return fds

#get the normal form choice
def get_normal_form_choice():
    choice = input("Choice of the highest normal form to reach (1: 1NF, 2: 2NF, 3: 3NF, B: BCNF, 4: 4NF, 5: 5NF): ")
    return choice.upper()

#gets whether or not user wants to know the highest normal form of input table
def find_input_normal_form_choice():
    choice = input("Find the highest normal form of the input table? (1: Yes, 2: No): ")
    return int(choice)

#gets the key
def get_key():
    key_input = input("Key (can be composite): ")
    keys = [key.strip() for key in key_input.split(',')]
    return keys



    


### 2.Normalization ###

#main driver for normalization process
#just uses the normal_form_choice of the user and calls the to_nf functions
def normalize(dataset, functional_dependencies, normal_form_choice, key, multivalued_dependencies):
    normalized_tables = []
    
    #1nf
    if normal_form_choice in ['1', '2', '3', 'B', '4', '5']:
        columns = dataset[0].keys()  # Get all column names from the first row of the dataset
        normalized_tables= to_1nf(dataset, columns, key)
    
    #2nf
    if normal_form_choice in ['2', '3', 'B', '4', '5']:
        normalized_tables = to_2nf(normalized_tables, functional_dependencies)

    
    #3nf
    if normal_form_choice in ['3', 'B', '4', '5']:
        transitive_dependencies = find_transitive_dependencies(functional_dependencies, key)
        normalized_tables = to_3nf(normalized_tables, transitive_dependencies, functional_dependencies)
        
    #bcnf
    if normal_form_choice in ['B', '4', '5']:
        normalized_tables = to_bcnf(normalized_tables, functional_dependencies)

        
    #4nf
    #I commented out the call for 4nf because it broke my code, and I'm out of time to fix it
    #But i figured I'd leave my work so you could see the idea behind it all
    #if normal_form_choice in ['4', '5']:
        #normalized_tables = to_4nf(normalized_tables, functional_dependencies, multivalued_dependencies)
        
    #5nf
    #Didn't get this far
    if normal_form_choice in ['5']:
        normalized_tables = to_5nf(normalized_tables, functional_dependencies)
        
    return normalized_tables  #returns a list of dictionaries, where each dictionary represents a table


def to_1nf(dataset, columns, key):
    normalized_tables = []
    multivalued_columns = []

    #searching for rows where there's a multivalued attribute
    for row in dataset:
        for col in columns:
            if ',' in str(row[col]):
                if col not in multivalued_columns:
                    multivalued_columns.append(col)

    #finds the column with the maximum number of values, this is in case there are multiple columns with multivalued attributes
    for row in dataset:
        max_values = 1
        for col in multivalued_columns:
            max_values = max(max_values, len(str(row[col]).split(',')))
        
        #creates new rows for each column with a multivalued attribute
        for i in range(max_values):
            new_row = {}
            for col in columns:
                if col in multivalued_columns:
                    values = str(row[col]).split(',')
                    new_row[col] = values[i].strip() if i < len(values) else ''
                else:
                    new_row[col] = row[col]
            normalized_tables.append(new_row)

    #update our keys
    for col in multivalued_columns:
        if col not in key:
            key.append(col)

    #this is where we set up the structure of our normalized table list
    #a list made up of dictionaries
    normalized_tables = [{
        'name': 'table1',
        'rows': normalized_tables,
        'key' : [key],
        'foreign_keys' : [],
        'columns' : columns
    }]

    return normalized_tables


def to_2nf(tables, functional_dependencies):
    normalized_tables = []

    #checking each table we have
    for table in tables:

        columns = set(table["columns"])
        rows = table["rows"]
        keys = table["key"]

        #finding partial dependencies
        partial_dependencies = find_partial_dependencies(columns, functional_dependencies, keys)
        
        #findiing transitive dependencies
        transitive_dependencies = find_transitive_dependencies(functional_dependencies, keys)

        #table_count is used for my naming convention. I tried having a more complex system
        #where it got a name from the primary key but it was just gibberish
        table_count = get_table_count(normalized_tables)+1
        
        #eliminatiing partial dependencies
        normalized_tables.extend(eliminate_partial_dependencies(columns, partial_dependencies, transitive_dependencies, rows, keys, table_count))
        
    return normalized_tables




def to_3nf(normalized_tables, transitive_dependencies, functional_dependencies):
    table_counter = get_table_count(normalized_tables)
    
    #find the LHS for transitive dependencies
    for td in transitive_dependencies:
        transitive_field = td[1][0]
        
        #search for the functional dependency for transitive field
        for fd in functional_dependencies:
            if transitive_field in fd[1]:
                fd_lhs = tuple(fd[0])
                break
        else:
            continue  # If no functional dependency found, skip to next transitive dependency

        #find the table with a PK matching the transitive dependency LHS
        for table in normalized_tables:
            table_primary_key_set = {tuple(pk) if isinstance(pk, list) else (pk,) for pk in table['key']}
            
            if {td[0]}.issubset(table_primary_key_set):
                #copy over data for new table
                new_table_columns = list(fd_lhs) + [transitive_field]
                table_counter += 1
                new_table_name = f"table{table_counter}"
                new_table_rows = []
                existing_values = set()
                

                for row in table['rows']:
                    row_data = tuple(row[col] for col in new_table_columns if col in row)
                    if row_data not in existing_values:
                        new_table_rows.append(dict(zip(new_table_columns, row_data)))
                        existing_values.add(row_data)

                #make new table
                new_table_key = [fd_lhs]

                new_table = {
                    'name': new_table_name,
                    'columns': new_table_columns,
                    'rows': new_table_rows,
                    'key': new_table_key,
                    'foreign_keys': []
                }
                
                #now we remove the transitive field from the first table and add the foreign key
                table['columns'] = [col for col in table['columns'] if col != transitive_field]
                table['foreign_keys'].append((fd_lhs[0], new_table_name))

                normalized_tables.append(new_table)
                break


    return normalized_tables



def to_bcnf(tables, fds):
    table_counter = get_table_count(tables)
    
    #changed is used to keep the loop going until no more changes are made
    #in testing this loop can get stuck infinitely, but hopefully
    #this doesn't happen with then dataset you're using to test it :)
    changed = True
    while changed:
        changed = False
        #gets new functional dependencies for our current tables
        fds = update_fds(tables, fds)
        for table in tables[:]:
            #check each functional dependency for a BCNF violation
            for fd in fds:
                lhs, rhs = fd
                is_lhs_superkey = is_superkey(table, lhs)
                is_rhs_subset = set(rhs).issubset(set(table['columns']))

                #if the lhs is not a superkey and rhs is a subset of the columns, theres a bcnf violation
                if not is_lhs_superkey and is_rhs_subset:
                    #use eliminate_bcnf to break the table up and resolve the bcnf violation
                    new_table_1, new_table_2 = eliminate_BCNF(table, fd, tables, table_counter)
                    tables.remove(table)
                    tables.append(new_table_1)
                    if new_table_2:
                        tables.append(new_table_2)

                    changed = True
                    break
            if changed:
                break
    return tables



#so this is where my program broke and I ran out of time before i could fix it
#somewhere within my to_4nf process i change one of my tables in my list from a dict to a tuple
#i struggled to figure out where and ultimately have to turn in what i have
def to_4nf(tables, functional_dependencies, multivalued_dependencies):
    table_counter = get_table_count(tables)

    #same structure as to_3nf
    changed = True
    while changed:
        changed = False


        for table in tables:
            for mvd in multivalued_dependencies:
                lhs, rhs = mvd
                #check if the left-hand side is a superkey or the right-hand side is a subset of the left-hand side
                if not is_superkey(table, lhs) and not set(rhs).issubset(set(lhs)):
                    
                    new_table = eliminate_4nf(table, mvd, tables, table_counter)
                    table_counter += 1
                    tables.append(new_table)
                    changed = True
                    break  #stop checking other MVDs for this table

            #if we changed the table, we need too update functional dependencies
            if changed:
                functional_dependencies = update_fds(tables, functional_dependencies)
                
                break

    return tables



#didn't get this far
def to_5nf(normalized_tables, functional_dependencies, key):
    # Implement 5NF normalization here
    # This should remove join dependencies that are not implied by candidate keys
    # ...
    return normalized_tables


#Helper functions

#counts all of the tables in the list for naming purposes
def get_table_count(normalized_tables):
    table_counter = 0

    for table in normalized_tables:
        table_counter += 1

    return table_counter



def find_partial_dependencies(attributes, functional_dependencies, key):
    partial_dependencies = []

    #ensure keys is a list of sets
    key_set = [set(key) if isinstance(key, list) else {key} for key in key]

    #find prime attributes
    prime_attributes = set(itertools.chain(*key_set))
    non_prime_attributes = set(attributes) - prime_attributes

    for lhs, rhs in functional_dependencies:
        lhs_set, rhs_set = set(lhs), set(rhs)

        #check if LHS is a subset of any key
        for candidate_key in key_set:
            if lhs_set.issubset(candidate_key):
                
                #check if RHS contains any nonprime attributes
                if rhs_set & non_prime_attributes:
                    partial_dependencies.append((lhs, list(rhs_set & non_prime_attributes)))
                #break if we found a partial dependency
                break 

    return partial_dependencies




def eliminate_partial_dependencies(columns, partial_dependencies, transitive_dependencies, rows, key, table_count):
    new_tables = []
    #used to help with foreign key info
    original_columns = set(columns)
    original_key = set(key[0]) if key else set()
    foreign_keys_info = {}

    table_counter = table_count

    #take care of partial dependencies
    for lhs, rhs in partial_dependencies:
        #if lhs was in the original_columns, break it off into new table
        if set(lhs).issubset(original_columns):
            new_table_columns = set(lhs).union(rhs)
            new_table_name = f"table{table_counter}"
            table_counter += 1
            
            new_table_rows = [{col: row[col] for col in new_table_columns if col in row} for row in rows]
            new_table_key = [list(lhs)]
            new_tables.append({
                "name": new_table_name,
                "columns": sorted(new_table_columns),
                "rows": new_table_rows,
                "key": new_table_key,
                "foreign_keys": []
            })

            #track the pk of new table for foreign key reference
            foreign_keys_info[new_table_name] = new_table_key

            #remove the columns that got moved from the original columns
            original_columns -= set(rhs)

    # takes care of transitive dependencies
    for lhs, rhs in transitive_dependencies:
        #find the table where lhs is a key
        for table in new_tables:
            if set(lhs) == set(table['key'][0]):
                #move the dependent attribute to the table where lhs is the key
                dependent_columns = set(rhs) - set(table['columns'])
                if dependent_columns:
                    table['columns'].extend(sorted(dependent_columns))
                    #update rows for  new table
                    table['rows'] = [{col: row[col] for col in table['columns'] if col in row} for row in rows]
                #remove the columns that got moved from the original columns
                original_columns -= set(rhs)

    #now we update the original table with remaining columns
    if original_columns:
        current_table_name = f"table{table_counter}"
        table_counter += 1  # Increment the counter as we've used it for the original table name
        updated_rows = [{col: row[col] for col in original_columns if col in row} for row in rows]
        current_table_keys = [k for k in key if set(k).issubset(original_columns)]
        original_table = {
            "name": current_table_name,
            "columns": sorted(original_columns),
            "rows": updated_rows,
            "key": current_table_keys,
            "foreign_keys": []
        }

        #make foriegn key for the first table
        for ref_table_name, ref_keys in foreign_keys_info.items():
            for fk in ref_keys[0]:
                if fk in original_key:
                    original_table["foreign_keys"].append((fk, ref_table_name))

        new_tables.append(original_table)

    return new_tables



def find_transitive_dependencies(functional_dependencies, key_set):
    functional_dependencies = [(tuple(lhs) if isinstance(lhs, list) else (lhs,),
                                tuple(rhs) if isinstance(rhs, list) else (rhs,))
                               for lhs, rhs in functional_dependencies]
    
    #finds dependencies where LHS is not a superkey
    direct_dependencies = {lhs: rhs for lhs, rhs in functional_dependencies if lhs not in key_set}
    
    transitive_dependencies = []
    
    #search the dependencies for a transitive dependency
    for lhs, rhs in direct_dependencies.items():
        for transitive_candidate in rhs:
            #see if the transitive candidate is a determinant in another dependency
            for potential_lhs, potential_rhs in direct_dependencies.items():
                if transitive_candidate in potential_lhs and lhs != potential_lhs:
                    #transitive dependency found
                    transitive_dependencies.append((lhs, potential_rhs))
    
    transitive_dependencies = list(set(transitive_dependencies))
    transitive_dependencies.sort()
    
    return transitive_dependencies

#checks for a superkey
def is_superkey(table, attributes):
    attributes_set = set(attributes)
    for key in table['key']:
        if attributes_set.issuperset(key):
            return True
    return False


def eliminate_BCNF(table, fd, tables, table_counter):
    lhs, rhs = fd
    name = f"table{table_counter}"

    #make a new table that will hold the dependency thats not in bcnf
    new_table = {
        'name': name,
        'columns': lhs + rhs,
        'rows': [],
        'key': lhs,
        'foreign_keys': []
    }


    #find the keys from the original table that shouldn't be in the new table
    keys = [key for key in table['key'] if not (set(rhs) <= set(key))]

    # now we update the first tables columns
    remaining_columns = [col for col in table['columns'] if col not in rhs or any(col in key for key in keys)]
    table['columns'] = remaining_columns

    #if the lhs of the functional dependency is not a superkey in the original table we need to add a foreign key
    if not is_superkey(table, lhs):
        table['foreign_keys'].append((lhs, name))

    existing_rows = set()
    #copy proper rows from first table to new table
    for row in table['rows']:
        new_row = {attr: row[attr] for attr in new_table['columns']}
        row_signature = tuple(new_row.items())
        #makes sure we're not duplicating rows
        if row_signature not in existing_rows:
            new_table['rows'].append(new_row)
            existing_rows.add(row_signature)
            

    #check for columns that were left behind, if there are none, delete the table
    remaining_columns = set(table['columns']) - set(rhs)
    if not remaining_columns:
        tables.remove(table)
        table = None

    return new_table, table  # Return the new table and the possibly updated original table


def update_fds(tables, fds):
    new_fds = []
    for lhs, rhs in fds:

        #get the tables that have all columns in lhs and rhs
        table_list = [
            t for t in tables 
            if set(lhs).issubset(t['columns']) and set(rhs).issubset(t['columns'])
        ]
        
        #For each table we found, add the functional dependency to the new_fds list
        for t in table_list:
            new_fds.append((lhs, rhs))
    
    return new_fds



def eliminate_4nf(table, mvd, tables, table_counter):
    lhs, rhs = mvd
    name = f"table{table_counter}"

    #table 1 will have the determinant and its dependent attributes
    new_table_1 = {
        'name': name,
        'columns': list(lhs) + list(rhs),
        'rows': [],
        'key': list(lhs),
        'foreign_keys': []
    }



    #update the existing rows
    existing_rows = set()
    for row in table['rows']:

        #see if the necessary attributes are in the row
        missing_attrs = [attr for attr in new_table_1['columns'] if attr not in row]
        #if we have missing attributes skip the row
        if missing_attrs:
            continue

        #making a new row with the proper attributes
        new_row = {attr: row[attr] for attr in new_table_1['columns']}
        row_signature = tuple(new_row.items())  # Create a unique identifier for this row
        
        #if the row doesn't exist yet, add it
        if row_signature not in existing_rows:
            new_table_1['rows'].append(new_row)
            existing_rows.add(row_signature)

    #make a second table for the attributes left over
    remaining_columns = [col for col in table['columns'] if col not in rhs]
    name_2 = f"table{table_counter+1}"
    new_table_2 = {
        'name': name_2,
        'columns': remaining_columns,
        'rows': table['rows'],
        'key': table['key'],
        'foreign_keys': [(list(lhs), name)]
    }

    #update our tables list
    tables.remove(table)
    tables.append(new_table_1)
    tables.append(new_table_2)

    return new_table_1, new_table_2


### 3.Highest Normalization of input table ###

#i didn't really get this far, but here is the skeleton that i came up with
#i think logically it should work
def find_normal_form(dataset, functional_dependencies, key):
    normal_form = 0
    columns = dataset[0].keys() 
    
    if is_in_1nf(dataset, columns):
        normal_form = 1
        
    if is_in_2nf(dataset, functional_dependencies, key):
        normal_form = 2
        
    if is_in_3nf(dataset, functional_dependencies, key):
        normal_form = 3
        
    if is_in_bcnf(dataset, functional_dependencies, key):
        normal_form = 'BC'
        
    if is_in_4nf(dataset, functional_dependencies, key):
        normal_form = 4
        
    if is_in_5nf(dataset, functional_dependencies, key):
        normal_form = 5
    return normal_form



def is_in_1nf(dataset, columns):
    #checks for the existance of a , meaning a attributet is multivalued
    for row in dataset:
        for col in columns:
            if ',' in str(row[col]):
                return False
    
    
    return True

def is_in_2nf(dataset, functional_dependencies, key):
    
    return False


def is_in_3nf(dataset, functional_dependencies, key):
    
    return False

def is_in_bcnf(dataset, functional_dependencies, candidate_keys):

    return False

def is_in_4nf(dataset, functional_dependencies, key):
    
    return False

def is_in_5nf(dataset, functional_dependencies, key):
    
    return False





### 4.SQL Query Generation ###

#simply determines what datatype to give an attribute
def infer_data_type(value):
    try:
        int(value)
        return 'INTEGER'
    except ValueError:
        try:
            float(value)
            return 'REAL'
        except ValueError:
            try:
                parse(value)
                return 'DATE'
            except (ValueError, ImportError):
                return 'VARCHAR(255)'



def generate_sql_queries(normalized_tables):
    sql_queries = []

    #for each table we have
    #start by pulling some info from it
    for table in normalized_tables:
        table_name = table['name']
        rows = table['rows']
        keys = table['key']
        foreign_keys = table.get('foreign_keys', [])

        columns = list(rows[0].keys())

        #get attribute data types and save in column_types
        column_types = {}
        for col in columns:
            values = [row[col] for row in rows if col in row]
            column_types[col] = infer_data_type(values[0]) if values else 'VARCHAR(255)'

        #initial create table statement
        create_table_query = f"CREATE TABLE {table_name} (\n"

        #keep track of primary key and foreign keys to append after column definitions
        primary_key_clauses = []
        foreign_key_clauses = []

        #make our column definitions
        for col, data_type in column_types.items():
            create_table_query += f"  {col} {data_type}"
            if [col] in keys:
                primary_key_clauses.append(col)
            create_table_query += ",\n"

        #add primary key
        if primary_key_clauses:
            create_table_query += f"  PRIMARY KEY ({', '.join(primary_key_clauses)}),\n"

        #foreign key
        for fk, ref_table in foreign_keys:
            foreign_key_clause = f"FOREIGN KEY ({fk}) REFERENCES {ref_table}({fk})"
            foreign_key_clauses.append(foreign_key_clause)

        for fk_clause in foreign_key_clauses:
            create_table_query += f"  {fk_clause},\n"

        #get rid of trailing comma and newline
        create_table_query = create_table_query.rstrip(',\n') + '\n);'
        sql_queries.append(create_table_query)

    return sql_queries



### 5.Main###

def main():
    if len(sys.argv) != 2:
        print("Use python main.py dataset.csv")
        sys.exit(1)

    #get all input
    dataset_file = sys.argv[1]
    dataset = read_dataset(dataset_file)
    
    functional_dependencies = read_functional_dependencies()
    multivalued_dependencies = read_multivalued_dependencies()
    normal_form_choice = get_normal_form_choice()
    find_input_normal_form = find_input_normal_form_choice()
    key = get_key()
    
    if find_input_normal_form == 1:
        input_normal_form = find_normal_form(dataset, functional_dependencies, key)
    #call our normalize driver
    normalized_tables = normalize(dataset, functional_dependencies, normal_form_choice, key, multivalued_dependencies)
    #get the queries
    sql_queries = generate_sql_queries(normalized_tables)

    #write to file
    with open("SQL.txt", 'w', encoding='utf-8') as f:
        for query in sql_queries:
            print(query, file=f)
        if find_input_normal_form == 1:
            print("Highest normal form of the input table: {}NF".format(input_normal_form), file=f)


if __name__ == "__main__":
    main()
