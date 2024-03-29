SYSTEM_MESSAGE = """
Tu es un spcialiste en assurance qui doit répondre à des questions sur les couvertures d'assurance.
Repond de manière assurée sans aucun doute. 
Répond en présicisant les exclusions et les limites qui s'applique à la question. 

Le context:
{context}

L'historique du chat:
{chat_history}
"""

HUMAN_MESSAGE = """Question: {question}"""


ANSWER_1 = """Selon l'article 111.1 de votre police d'assurance, les dommages causés par l'eau s'échappant des installations et appareils raccordés sont couverts, ce qui inclurait le débordement de l'eau de la douche qui a endommagé votre machine à laver.\n\nCependant, l'article 111.2 ne mentionne pas explicitement la négligence comme une exclusion. Néanmoins, dans la pratique, si l'assureur détermine que le débordement est dû à une négligence de votre part, comme par exemple si vous avez intentionnellement laissé l'eau couler sans surveillance, ils pourraient considérer cela comme une omission de mesures de défense ou un entretien défectueux, ce qui pourrait potentiellement exclure la couverture.\n\nIl est donc crucial de vérifier l'ensemble de votre contrat d'assurance pour toute clause qui pourrait traiter de la négligence ou de l'entretien défectueux. Si une telle clause est présente et que l'assureur établit que la négligence est la cause du sinistre, la couverture pourrait être refusée.\n\nPour obtenir une réponse définitive, vous devriez contacter votre assureur et fournir tous les détails de l'incident. Ils seront en mesure d'évaluer si la négligence est un facteur dans ce cas et si elle affecte votre couverture."""

ANSWER_2 = """Si la négligence de votre part a entraîné le débordement de l'eau, cela pourrait potentiellement affecter la couverture de votre assurance. Bien que l'article 111.1 couvre les dommages causés par l'eau s'échappant des installations et appareils raccordés, y compris les dégâts d'eau dus à un débordement de la douche, il est important de considérer les conditions générales de votre contrat d'assurance.\n\nLes polices d'assurance exigent souvent que le preneur d'assurance prenne des mesures raisonnables pour prévenir les dommages. Si l'assureur détermine que le débordement est survenu en raison de votre négligence, comme par exemple ne pas fermer le robinet ou laisser la douche sans surveillance, cela pourrait être interprété comme une omission de mesures de défense ou un entretien défectueux, ce qui pourrait exclure la couverture selon l'article 111.2.\n\nIl est donc essentiel de vérifier les termes spécifiques de votre contrat d'assurance pour voir si la négligence est mentionnée comme une exclusion. Si c'est le cas, et que l'assureur établit que la négligence est la cause directe du sinistre, ils pourraient refuser de couvrir les dommages.\n\nPour clarifier la situation, vous devriez contacter votre assureur, expliquer les circonstances du débordement et demander une évaluation de votre couverture dans ce contexte spécifique."""

ANSWER_3 = """Bien sûr, je vais clarifier les informations concernant la couverture de votre assurance pour les dommages causés par l'eau qui a débordé de la douche.\n\nSelon l'article 111.1 de votre police d'assurance, les dommages causés par des liquides s'écoulant des installations et appareils raccordés sont effectivement couverts. Cela inclut l'eau provenant de votre douche qui a débordé et causé un court-circuit à votre machine à laver. La couverture comprend les frais de réparation ou de remplacement des appareils endommagés par l'eau.\n\nCependant, il est important de prendre en compte les restrictions de l'étendue de l'assurance mentionnées dans l'article 111.2. Les exclusions pertinentes pour votre situation pourraient être les dommages causés par l'entretien défectueux des bâtiments ou l'omission de mesures de défense. Si le débordement de l'eau de la douche est dû à un manque d'entretien ou à une négligence de votre part, l'assureur pourrait potentiellement refuser la couverture.\n\nIl n'y a pas d'exclusion spécifique dans l'article 111.2 qui mentionne explicitement le débordement de l'eau de la douche comme étant exclu. Par conséquent, en l'absence d'autres exclusions ou conditions dans votre contrat d'assurance, les dommages causés par l'eau de la douche qui a débordé devraient être couverts.\n\nPour confirmer votre couverture et entamer le processus de réclamation, vous devriez contacter votre assureur dès que possible. Ils examineront les détails de l'incident et vous informeront des démarches à suivre pour la prise en charge des dommages subis par votre machine à laver."""

ANSWER_4 = "Bonjour"

ANSWER_5 = "Perte, détérioration, destruction"

ANSWER_6 = "Temporelle: Pendant la durée de l'assurance. Territoriale: À la maison, extensions possibles."

ANSWER_7 = "Non couvert: Vol simple hors domicile sans assurances complémentaires, perte/égarement, événements exclus (guerre, fission nucléaire...)"

ANSWER_8 = "Cette table résume les principaux éléments de couverture et de restriction liés au vol dans les packages d'assurance CLASSIC et ALL RISK, incluant les franchises applicables et la validité territoriale et temporelle des couvertures."

ANSWER_9 = "Exclusion du vol simple dans le cadre de l’assurance externe (sauf avec assurances complémentaires), de valeurs pécuniaires, et des dommages résultant de la perte ou de l’égarement. Restriction sur la couverture des bijoux en cas de vol à la maison et avec effraction (limitation à 20% de la somme d’assurance, max CHF 30’000) sauf conditions spécifiques pour le coffre-fort. Exclusions générales incluant les véhicules à moteur, bateaux, aéronefs, cryptomonnaies, et les événements non assurés comme guerre, fission nucléaire, etc."