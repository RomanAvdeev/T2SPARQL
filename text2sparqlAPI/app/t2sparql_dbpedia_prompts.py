NER_PROMPT = """
Examples:

1. Input: "Who are relatives of Ozzy Osbourne and Kelly Osbourne?"
Output:
Let's think step by step. In the question "Who are relatives of Ozzy Osbourne and Kelly Osbourne?", we are asked: "find people related to both Ozzy Osbourne and Kelly Osbourne".
so we need to identify: relatives, persons.
The entities are: Ozzy Osbourne, Kelly Osbourne.
So the intermediary_question is: Whose <relativess> are <Ozzy Osbourne> and <Kelly Osbourne>?

2. Input: "What is the television show whose previous work is The Spirit of Christmas (short film)?"
Output:
Let's think step by step. In the question "What is the television show whose previous work is The Spirit of Christmas (short film)?", we are asked: "find TV shows connected to The Spirit of Christmas short film".
so we need to identify: television show, previous work, film.
The entities are: The Spirit of Christmas (short film).
So the intermediary_question is: What is the <television show> whose <previous work> is <The Spirit of Christmas (short film)>?

3. Input: "Which office holder's governor is Charles Willing Byrd and has final resting place in North Bend, Ohio?"
Output:
Let's think step by step. In the question "Which office holder's governor is Charles Willing Byrd and has final resting place in North Bend, Ohio?", we are asked: "find political figures governed by Charles Willing Byrd who are buried in North Bend".
so we need to identify: office holder, governor, resting place, person, location.
The entities are: Charles Willing Byrd, North Bend, Ohio.
So the intermediary_question is: What is the <office holder> whose <governor> is <Charles Willing Byrd> and <restingplace> is <North Bend, Ohio>?

4. Input: "What is the allegiance of John Kotelawala?"
Output:
Let's think step by step. In the question "What is the allegiance of John Kotelawala?", we are asked: "find political allegiance of John Kotelawala".
so we need to identify: allegiance, person.
The entities are: John Kotelawala.
So the intermediary_question is: What is the <allegiance> of John Kotelawala?

5. Input: "Where is the headquarters of the public transit system which owns the American Boulevard (Metro Transit station)?"
Output:
Let's think step by step. In the question "Where is the headquarters of the public transit system which owns the American Boulevard (Metro Transit station)?", we are asked: "find location of transit agency managing American Boulevard station".
so we need to identify: headquarters, public transit system, owning organization, station.
The entities are: American Boulevard (Metro Transit station).
So the intermediary_question is: What is the <headquarters> of the <public transit system> which is the <owning organisation> of <American Boulevard (Metro Transit station)>?

Key Requirements:
- Maintain EXACT output format including punctuation and spacing
- Use same entity tags as examples (<relativess>, <restingplace> etc.)
- Keep original capitalization in entity names
- Never add additional explanations outside the template
"""

URI_GENERATION_PROMPT = """
Examples with Reasoning:

1. Input:
   Question: "Who wrote the play in which Blanche DuBois is a character?"
   Intermediary: "What is the <writer> of the <play> whose <characters> is <Blanche DuBois>?"

   Output:
   - <writer> : http://dbpedia.org/ontology/author
   - <play> : http://dbpedia.org/ontology/Play
   - <characters> : http://dbpedia.org/ontology/character
   - <Blanche DuBois> : http://dbpedia.org/resource/Blanche_DuBois

2. Input:
   Question: "Which football team is in a city where A J Clark was a builder?"
   Intermediary: "What is the <american football Team> whose <city>'s <builder> is <A. James Clark>?"

   Output:
   - <american football Team> : http://dbpedia.org/ontology/AmericanFootballTeam
   - <city> : http://dbpedia.org/ontology/City
   - <builder> : http://dbpedia.org/property/builder
   - <A. James Clark> : http://dbpedia.org/resource/A._James_Clark

3. Input:
   Question: "Name a person who was educated in Humes High School?"
   Intermediary: "Who is the <person> whose <alumna of> is <Humes High School>?"

   Output:
   - <person> : http://dbpedia.org/ontology/Person
   - <alumna of> : http://dbpedia.org/ontology/almaMater
   - <Humes High School> : http://dbpedia.org/resource/Humes_High_School

4. Input:
   Question: "Is Ella Fitzgerald associated with Mickey Roker?"
   Intermediary: "Is <Ella Fitzgerald> the <associated band> of <Mickey Roker>?"

   Output:
   - <Ella Fitzgerald> : http://dbpedia.org/resource/Ella_Fitzgerald
   - <associated band> : http://dbpedia.org/ontology/associatedBand
   - <Mickey Roker> : http://dbpedia.org/resource/Mickey_Roker

5. Input:
   Question: "Who founded a company which served Mid Wales?"
   Intermediary: "What is the <founded by> of the <company> whose <region served> is <Mid Wales>?"

   Output:
   - <founded by> : http://dbpedia.org/ontology/founder
   - <company> : http://dbpedia.org/ontology/Company
   - <region served> : http://dbpedia.org/property/regionServed
   - <Mid Wales> : http://dbpedia.org/resource/Mid_Wales

6. Input:
   Question: "Which baseball team is owned by Robert Nutting?"
   Intermediary: "What is the <baseball team> whose <stockholder> is <Robert Nutting>?"

   Output:
   - <baseball team> : http://dbpedia.org/ontology/BaseballTeam
   - <stockholder> : http://dbpedia.org/ontology/owner
   - <Robert Nutting> : http://dbpedia.org/resource/Robert_Nutting

7. Input:
   Question: "Give the name of the river with source place as Australian Alps and has mouth place as Goolwa, a place in South Australia?"
   Intermediary: "What is the <river> whose <source place> is <Australian Alps> and <mouth place> is <Goolwa, South Australia>?"

   Output:
   - <river> : http://dbpedia.org/ontology/River
   - <source place> : http://dbpedia.org/ontology/sourcePlace
   - <mouth place> : http://dbpedia.org/ontology/mouthPlace
   - <Australian Alps> : http://dbpedia.org/resource/Australian_Alps
   - <Goolwa, South Australia> : http://dbpedia.org/resource/Goolwa,_South_Australia

Verification Checklist:
1. For resources: Check exact name matches on DBpedia
2. For classes: Ensure most specific available type is used
3. For properties: Always try ontology namespace first
4. Special cases:
   - Personal names with initials/middle names
   - Geographic names with regional qualifiers
   - Technical terms with special characters
"""

SPARQL_GENERATION_PROMPT = """
Input:
Original Question: "List the resting place of the people who served in Norwalk Trainband"
Question with Entities: "List the <restingplace> of the <politicians> whose <military unit> is <Norwalk Trainband>"
DBpedia URIs:
- <Norwalk Trainband> : http://dbpedia.org/resource/Norwalk_Trainband
- <militaryUnit> : http://dbpedia.org/ontology/militaryUnit
- <restingplace> : http://dbpedia.org/property/restingplace
- <Person> : http://dbpedia.org/ontology/Person

Thought Process:
Let's think step by step. In the question "List the resting place of the people who served in Norwalk Trainband", we are asked:
1. "the resting place" → we need property = [http://dbpedia.org/property/restingplace]
2. "people who served in Norwalk Trainband" → we need:
   - class restriction = [http://dbpedia.org/ontology/Person] (to identify people)
   - military service property = [http://dbpedia.org/ontology/militaryUnit]
   - specific military unit = [http://dbpedia.org/resource/Norwalk_Trainband]
3. We need to connect these through a variable (?x) representing the people
4. Final output should be the resting places (?uri)

SPARQL:
SELECT DISTINCT ?uri WHERE {
  ?x <http://dbpedia.org/ontology/militaryUnit> <http://dbpedia.org/resource/Norwalk_Trainband> .
  ?x <http://dbpedia.org/property/restingplace> ?uri .
  ?x a <http://dbpedia.org/ontology/Person> .
}

Input:
Original Question: "What are the broadcast areas of Mauritius Broadcasting Corporation"
Question with Entities: "What are the <broadcast area> of <Mauritius Broadcasting Corporation>"
DBpedia URIs:
- <Mauritius Broadcasting Corporation> : http://dbpedia.org/resource/Mauritius_Broadcasting_Corporation
- <broadcastArea> : http://dbpedia.org/property/broadcastArea

Thought Process:
Let's think step by step. In the question "What are the broadcast areas of Mauritius Broadcasting Corporation", we are asked:
1. "broadcast areas" → we need property = [http://dbpedia.org/property/broadcastArea]
2. "of Mauritius Broadcasting Corporation" → we need specific entity = [http://dbpedia.org/resource/Mauritius_Broadcasting_Corporation]
3. This is a direct property lookup without need for variables or class restrictions
4. Final output should be the broadcast areas (?uri)

SPARQL:
SELECT DISTINCT ?uri WHERE {
  <http://dbpedia.org/resource/Mauritius_Broadcasting_Corporation> <http://dbpedia.org/property/broadcastArea> ?uri .
}

Input:
Original Question: "Which company released the software RenderMan"
Question with Entities: "What is the <company> whose <products> is <RenderMan (software)>"
DBpedia URIs:
- <RenderMan (software)> : http://dbpedia.org/resource/RenderMan_(software)
- <products> : http://dbpedia.org/property/products
- <Company> : http://dbpedia.org/ontology/Company

Thought Process:
Let's think step by step. In the question "Which company released the software RenderMan", we are asked:
1. "company" → we need class restriction = [http://dbpedia.org/ontology/Company]
2. "released the software RenderMan" → we need:
   - release relationship property = [http://dbpedia.org/property/products]
   - specific product = [http://dbpedia.org/resource/RenderMan_(software)]
3. We need to find entities (?uri) that are Companies and have RenderMan as product
4. Final output should be the company/companies (?uri)

SPARQL:
SELECT DISTINCT ?uri WHERE {
  ?uri <http://dbpedia.org/property/products> <http://dbpedia.org/resource/RenderMan_(software)> .
  ?uri a <http://dbpedia.org/ontology/Company> .
}

Input:
Original Question: "Does Mumbai manage the railway line going to the Daund railway junction"
Question with Entities: "Is <Mumbai> the <serving railway line> of <Daund Junction railway station>"
DBpedia URIs:
- <Daund Junction railway station> : http://dbpedia.org/resource/Daund_Junction_railway_station
- <servingRailwayLine> : http://dbpedia.org/ontology/servingRailwayLine
- <Mumbai> : http://dbpedia.org/resource/Mumbai

Thought Process:
Let's think step by step. In the question "Does Mumbai manage the railway line going to the Daund railway junction", we are asked:
1. This is a yes/no question → we need ASK query
2. We need to check if:
   - subject = [http://dbpedia.org/resource/Daund_Junction_railway_station]
   - property = [http://dbpedia.org/ontology/servingRailwayLine]
   - object = [http://dbpedia.org/resource/Mumbai]
3. No variables needed, just a direct triple check
4. Query should return true/false whether this exact triple exists

SPARQL:
ASK WHERE {
  <http://dbpedia.org/resource/Daund_Junction_railway_station> <http://dbpedia.org/ontology/servingRailwayLine> <http://dbpedia.org/resource/Mumbai> .
}

# Example 1: Cities in Germany with population > 1 million

Input:
Original Question: "Give me all cities in Germany with more than 1 million inhabitants"
Question with Entities: "Give me all <cities> in <Germany> with <population> more than <1000000>"
DBpedia URIs:
- <Germany> : http://dbpedia.org/resource/Germany
- <cities> : http://dbpedia.org/ontology/City
- <population> : http://dbpedia.org/ontology/populationTotal

Thought Process:
Let's think step by step. In the question "Give me all cities in Germany with more than 1 million inhabitants", we are asked:
1. "cities" → we need class restriction = [http://dbpedia.org/ontology/City]
2. "in Germany" → we need country relationship = [http://dbpedia.org/ontology/country]
3. "with more than 1 million inhabitants" → we need:
   - population property = [http://dbpedia.org/ontology/populationTotal]
   - numeric filter > 1000000
4. We need to connect these through a variable (?city)
5. Final output should be the cities (?city)

SPARQL:
SELECT DISTINCT ?city WHERE {
  ?city a <http://dbpedia.org/ontology/City> .
  ?city <http://dbpedia.org/ontology/country> <http://dbpedia.org/resource/Germany> .
  ?city <http://dbpedia.org/ontology/populationTotal> ?population .
  FILTER (?population > 1000000)
}


# Example 2: Authors of 'The God Delusion'

Input:
Original Question: "Who wrote the book 'The God Delusion'?"
Question with Entities: "Who are the <authors> of <The God Delusion>"
DBpedia URIs:
- <The God Delusion> : http://dbpedia.org/resource/The_God_Delusion
- <authors> : http://dbpedia.org/ontology/author

Thought Process:
Let's think step by step. In the question "Who wrote the book 'The God Delusion'?", we are asked:
1. "wrote" → we need author property = [http://dbpedia.org/ontology/author]
2. "the book 'The God Delusion'" → we need specific resource = [http://dbpedia.org/resource/The_God_Delusion]
3. This is a direct property lookup with the subject known
4. Final output should be the author(s) (?author)

SPARQL:
SELECT DISTINCT ?author WHERE {
  <http://dbpedia.org/resource/The_God_Delusion> <http://dbpedia.org/ontology/author> ?author .
}


# Example 3: Airports served by Lufthansa

Input:
Original Question: "List all airports served by Lufthansa"
Question with Entities: "List all <airports> whose <serving airline> is <Lufthansa>"
DBpedia URIs:
- <Lufthansa> : http://dbpedia.org/resource/Lufthansa
- <airports> : http://dbpedia.org/ontology/Airport
- <serving airline> : http://dbpedia.org/ontology/airline

Thought Process:
Let's think step by step. In the question "List all airports served by Lufthansa", we are asked:
1. "airports" → we need class restriction = [http://dbpedia.org/ontology/Airport]
2. "served by Lufthansa" → we need:
   - airline relationship = [http://dbpedia.org/ontology/airline]
   - specific airline = [http://dbpedia.org/resource/Lufthansa]
3. We need to find entities (?airport) that are Airports and have Lufthansa as airline
4. Final output should be the airports (?airport)

SPARQL:
SELECT DISTINCT ?airport WHERE {
  ?airport a <http://dbpedia.org/ontology/Airport> .
  ?airport <http://dbpedia.org/ontology/airline> <http://dbpedia.org/resource/Lufthansa> .
}


# Example 4: Rivers through Germany and France

Input:
Original Question: "Which rivers flow through both Germany and France?"
Question with Entities: "Which <rivers> have <flow through> both <Germany> and <France>"
DBpedia URIs:
- <Germany> : http://dbpedia.org/resource/Germany
- <France> : http://dbpedia.org/resource/France
- <rivers> : http://dbpedia.org/ontology/River
- <flow through> : http://dbpedia.org/ontology/country

Thought Process:
Let's think step by step. In the question "Which rivers flow through both Germany and France?", we are asked:
1. "rivers" → we need class restriction = [http://dbpedia.org/ontology/River]
2. "flow through both Germany and France" → we need:
   - country relationship = [http://dbpedia.org/ontology/country]
   - for both countries = [http://dbpedia.org/resource/Germany] and [http://dbpedia.org/resource/France]
3. We need to find entities (?river) that are Rivers and have both countries
4. Final output should be the rivers (?river)

SPARQL:
SELECT DISTINCT ?river WHERE {
  ?river a <http://dbpedia.org/ontology/River> .
  ?river <http://dbpedia.org/ontology/country> <http://dbpedia.org/resource/Germany> .
  ?river <http://dbpedia.org/ontology/country> <http://dbpedia.org/resource/France> .
}


# Example 5: Population of Paris

Input:
Original Question: "How many inhabitants does Paris have?"
Question with Entities: "What is the <population> of <Paris>"
DBpedia URIs:
- <Paris> : http://dbpedia.org/resource/Paris
- <population> : http://dbpedia.org/ontology/populationTotal

Thought Process:
Let's think step by step. In the question "How many inhabitants does Paris have?", we are asked:
1. "inhabitants" → we need population property = [http://dbpedia.org/ontology/populationTotal]
2. "Paris" → we need specific resource = [http://dbpedia.org/resource/Paris]
3. This is a direct property value lookup
4. Final output should be the population value (?population)

SPARQL:
SELECT ?population WHERE {
  <http://dbpedia.org/resource/Paris> <http://dbpedia.org/ontology/populationTotal> ?population .
}

# Example 6: Films by Nolan starring Bale
Input:
Original Question: "Give me all films directed by Christopher Nolan and starring Christian Bale"
Question with Entities: "Give me all <films> whose <director> is <Christopher Nolan> and <starring> is <Christian Bale>"
DBpedia URIs:
- <Christopher Nolan> : http://dbpedia.org/resource/Christopher_Nolan
- <Christian Bale> : http://dbpedia.org/resource/Christian_Bale
- <films> : http://dbpedia.org/ontology/Film
- <director> : http://dbpedia.org/ontology/director
- <starring> : http://dbpedia.org/ontology/starring

Thought Process:
Let's think step by step. In the question "Give me all films directed by Christopher Nolan and starring Christian Bale", we are asked:
1. "films" → we need class restriction = [http://dbpedia.org/ontology/Film]
2. "directed by Christopher Nolan" → we need:
   - director property = [http://dbpedia.org/ontology/director]
   - specific director = [http://dbpedia.org/resource/Christopher_Nolan]
3. "starring Christian Bale" → we need:
   - starring property = [http://dbpedia.org/ontology/starring]
   - specific actor = [http://dbpedia.org/resource/Christian_Bale]
4. We need to find entities (?film) that match all conditions
5. Final output should be the films (?film)

SPARQL:
SELECT DISTINCT ?film WHERE {
  ?film a <http://dbpedia.org/ontology/Film> .
  ?film <http://dbpedia.org/ontology/director> <http://dbpedia.org/resource/Christopher_Nolan> .
  ?film <http://dbpedia.org/ontology/starring> <http://dbpedia.org/resource/Christian_Bale> .
}
"""

QUERY_REPAIR_PROMPT = """Fix this SPARQL query based on the execution error while preserving intent. Return ONLY the fixed SPARQL query.

Error Context: {error}

Repair Strategies:
1. For empty results:
   - Verify all entity URIs exist in DBpedia
   - Try alternative properties/classes when possible:
     * Check ontology for related properties (e.g., 'spouse' → 'partner')
     * Use superclasses when specific class fails (e.g., 'SoccerPlayer' → 'Athlete')
   - Relax strict filters (= → contains, exact matches → partial)

2. For syntax errors:
   - Fix malformed SPARQL syntax
   - Ensure proper variable binding
   - Correct prefix declarations

3. URI Replacement Rules:
   - For resources: try alternative names/redirects (e.g., 'New York' → 'New_York_City')
   - For properties: try ontology vs. property namespace (dbo: vs. dbp:)
   - For classes: use more general types when specific fails

4. Always:
   - Preserve the original query intent
   - Maintain all essential constraints
   - Keep variable names consistent

Input Query:
{original_query}

Context:
- Question: {original_question}
- Tagged: {tagged_question}
- Original URIs: {uris}

Output ONLY the corrected SPARQL query with NO additional text:"""


QUESTION_CLARIFY = """
Act as a SPARQL query pre-processor. Your task is to clarify ambiguous / incomplete user question (written below) to ensure they can be accurately translated into a SPARQL query. Focus on disambiguating place names, adding missing context, and correcting assumptions.

GIVEN QUESTION: {question}

Examples:
1) Input: "Washington is the capital of what country?"
Output: "Washington DC is the capital of what country?" (Clarify: Washington state vs. Washington DC)

2) Input: "Apple revenue in 2020."
Output: "What was Apple Inc.'s revenue in 2020?" (Clarify: Apple the company vs. apple the fruit)

3) Input: "USA President during WWII."
Output: "Who was the president of the United States during World War II?" (Clarify: country name + World War)
"""
