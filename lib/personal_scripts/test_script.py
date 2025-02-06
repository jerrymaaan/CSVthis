def test_script(dataframe):  # gets a copy of the original dataframe which contains data from CSV file

    # change this test_script to perform your own calculation here

    # creates empty lists to save new values
    # (better performance to add the list to a dataframe after the loop
    # instead of adding new values to a dataframe each iteration)
    some_list = []

    for i in range(len(dataframe)):
        some_list.append(i)

    # adds list to dataframe after iteration
    dataframe["some_column"] = some_list

    return dataframe["some_column"]  # has to return column of a dataframe; list will throw an error
