
class StringQueryTool:
    """ Takes a query string and evaluates whether the pattern matches given haystack
    Example query strings: "this & that", "this, that", "(foo,bar)&(spam,eggs)"
    """
    ILLEGAL_CHARS = ["{","}","[","]"]

    def __init__(self, query_string, or_separator=",", and_separator="&"):
        if or_separator in self.ILLEGAL_CHARS:
            raise IllegalCharacterException("Illegal character chosen for the or_separator")
        if and_separator in self.ILLEGAL_CHARS:
            raise IllegalCharacterException("Illegal character chosen for the and_separator")
            
        for char in self.ILLEGAL_CHARS:
            if char in query_string:
                raise IllegalCharacterException("Illegal character in the query_string: '%s'" %char)

        self.or_separator=or_separator
        self.and_separator=and_separator
        self.set_query_string(query_string)

    def set_query_string(self, query_string):
        """ Validate and set the query_string and query properties """
        self.query = self._prepare_query_string(query_string)
        self.query_string = query_string

    def _prepare_query_string(self, query_string):
        """ Convert the query string into the correct data structure so it can be used to search haystacks"""
        # Order of operations: brackets, AND, OR
        query_string = query_string.strip()
        query = []
        query_map = {}

        # Handle the brackets first
        #TODO: add support for nested brackets
        start = query_string.find("(")
        if start > -1:
            while start < len(query_string):
                # Check that the previous character is either a separator or the beginning of the string
                if start > 0 and query_string[start-1] not in [self.or_separator, self.and_separator]:
                    raise InvalidQueryException("Bracket sections not properly separated.")

                # Find the accompanying closing bracket
                end = query_string.find(")", start)
                if end == -1: 
                    raise InvalidQueryException("Missing closing bracket in query string.")

                # Check that there are no nested brackets
                query_part = query_string[start+1:end]
                if "(" in query_part or ")" in query_part:
                    raise InvalidQueryException("Nested brackets are not currently supported.")

                # Convert query_part into a dictionary with the relevant operator
                query_node = self._create_dict(query_part)

                # Replace the bracket section with a placeholder
                query_string = query_string[:start] + "{%s}" %(len(query_map)) + query_string[end+1:]
                map_key = "{%s}" %len(query_map)
                query_map[map_key] = query_node

                cont = end - len(query_part) + len(str(len(query_map)-1))
                start = query_string.find("(",cont)
                if start == -1:
                    break

        query_node = self._create_dict(query_string)
        query.append(query_node)
        query = self._remap_query(query,query_map)
        print(query)
        return query

    def _create_dict(self, query_string):
        # Check that no brackets exist in this part of the query string
        if "(" in query_string or ")" in query_string:
            raise InvalidQueryException("Nested brackets are not currently supported")

        # Separate OR operator first (lowest precedence)
        query_node = {}
        if self.or_separator in query_string:
            or_parts = [x.strip() for x in query_string.split(self.or_separator)]

            # Separate AND operator next and add the dictionary into or_parts
            i=0
            while i < len(or_parts):
                if self.and_separator in or_parts[i]:
                    or_parts[i] = {"and":[x.strip() for x in or_parts[i].split(self.and_separator) if x.strip() != ""]}
                i+=1

            query_node["or"] = []
            for part in or_parts:
                query_node["or"].append(part)

        else:
            query_node["and"] = [x.strip() for x in query_string.split(self.and_separator) if x.strip() != ""]

        return query_node

    def _remap_query(self, query, query_map):
        """ Remap the placeholders in the query """
        i=0
        while i < len(query):
            if isinstance(query[i],dict):
                for key in query[i]:
                    if isinstance(query[i][key],list):
                        query[i][key] = self._remap_query(query[i][key], query_map)
            elif isinstance(query[i],list):
                # Shouldn't ever go down this route, but if it does, just loop through the list again
                query[i] = self._remap_query(query[i], query_map)
            else:
                if query[i] in query_map:
                    # Replace the placeholder with the original query
                    query[i] = query_map[query[i]]
            i+=1
        
        return query

    def gen_stmt(self):
        """ Build a query statement in readable text and return it """
        stmt = ""
        for query_part in self.query:
            if isinstance(query_part,dict):
                stmt += self._from_dict(query_part)
        return stmt
        
    def _from_dict(self, query_part):
        stmt = ""
        operators = ["and","or"]
        first=True
        for operator in operators:
            if operator in query_part:
                if not first:
                    stmt += " %s " %operator
                stmt += self._add_clause(query_part[operator],operator)
                first=False
        return stmt

    def _add_clause(self, query_part, operator):
        stmt = "("
        first=True
        for ele in query_part:
            if not first:
                stmt += " %s " %operator
            if isinstance(ele,dict):
                stmt += self._from_dict(ele)
            else:
                stmt += ele
            first=False
        stmt += ")"
        return stmt

    def is_match(self, haystack):
        """ Evaluate whether the stored query string matches a given haystack """
        matched = True
        for query_part in self.query:
            if isinstance(query_part,dict):
                matched = self._match_dict(query_part, haystack)
            else:
                raise Exception("Query is in an incorrect format")
        return matched

    def _match_dict(self, pattern_dict, haystack):
        matched = True
        operators = ["and","or"]
        for operator in operators:
            if operator in pattern_dict:
                matched = self._match_list(operator, pattern_dict[operator], haystack)
        return matched

    def _match_list(self, operator, pattern_list, haystack):
        if operator == "and":
            matched = True
            for ele in pattern_list:
                if isinstance(ele,dict):
                    if not self._match_dict(ele, haystack): return False
                elif isinstance(ele,list):
                    raise InvalidQueryException("Query incorrectly formatted")
                else:
                    if ele.lower() not in haystack.lower(): return False
        elif operator == "or":
            matched = False
            for ele in pattern_list:
                if isinstance(ele,dict):
                    if self._match_dict(ele, haystack): return True
                else:
                    if ele.lower() in haystack.lower(): return True
        else:
            raise InvalidQueryException("Unrecognised operator '%s'" %operator)
        return matched

class InvalidQueryException(Exception):
    pass

class IllegalCharacterException(Exception):
    pass

class QueryMapException(Exception):
    pass