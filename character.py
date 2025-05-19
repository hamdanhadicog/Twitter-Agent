from dataclasses import dataclass

@dataclass
class Character:
    name: str
    description: str
    ct0: str
    auth_token: str

    # Class-level list to store all created characters
    all_characters = []

    def __post_init__(self):
        # Automatically add the new instance to the list
        self.all_characters.append(self)

#Verified
character1 = Character(
    name="Alex Harper",
    description="An AI assistant that helps you with your tasks.",
    ct0="5ef956ee6cb46dfacee77d627853028e6ff8e20c508011ac2d6160ce85796e3f28e540e6b17e8d31e22f511aa5e33317feae949fc72bb82d8e4a074548e627730e3f5d85e875eb32bd1b96f2289e5525",
    auth_token="0ac088d52caaa63be357dd3d80d8fe618bad0946"
)

#Verified
character2 = Character(
    name="Ahmad Hashem",
    description="An AI assistant that helps you with your tasks.",
    ct0="a145a5a027edea2ab6fbb6946eb5838d55d04a0448112e4d60fabb0fee04776c636d610f14591b86a53cf4c5bd596c823ab00ecb99cbd9064dfeb22de4619a49b08463e8621f41f0e4ac7f9753e80970",
    auth_token="380065ba1bb86ca2a84d246c8eef912d539ebbb0"
)

#Verified
character3 = Character(
    name="Elissa",
    description="An AI assistant that helps you with your tasks.",
    ct0="a145a5a027edea2ab6fbb6946eb5838d55d04a0448112e4d60fabb0fee04776c636d610f14591b86a53cf4c5bd596c823ab00ecb99cbd9064dfeb22de4619a49b08463e8621f41f0e4ac7f9753e80970",
    auth_token="689fe83c10643ca607b83fcbe174b60e7dfb51ad"
)

#Verified
character4 = Character(
    name="Lara Hamdan",
    description="An AI assistant that helps you with your tasks.",
    ct0="e4f591c07733e457f257247ec36f133b5f5a9003c72f6d49239acccb5524ddb80f98a392fd68b7abb935aa7bc83abbb4f182ace7ea0e6049b5d044339f3cf85c41ea0b4fdd45bcb8b2da415dbfb719cf",
    auth_token="179b064a44b6d5ecfa04a61a954a238db1068c8e"
)

chacharacter5 = Character(
    name="Elissa Karam",
    description="An AI assistant that helps you with your tasks.",
    ct0="3070ca17d3344a6cbe18452e2410c6f07b0513794e9fdfb8ea79fb7d229aa46abd966bc1ac2baaa4d530da6aad0ebbe49949598979cc1a6419cf0c18011dbc682ba604934f1dd481f4fe714c0843ce56",
    auth_token="dcfb1bfc8c95eb9911b0b520e0e3f5d3290240eb"
)


chacharacter6 = Character(
    name="Khalid",
    description="An AI assistant that helps you with your tasks.",
    ct0="59487b3abe5f226fdf7812407e70a192b2fa9a0297c431bb1b5e86ba159bb0866509e6b5e4b44d3cff2ed1bb194e8568aa10fd17855e6896388db772097148b434a48fccd126d96fb8ccf1b10c41b467",
    auth_token="fbd6f0889a7f8c0cbc07e93be5bbcbebb70def6a"
)

chacharacter7 = Character(
    name="Hasan Zubaidi",
    description="An AI assistant that helps you with your tasks.",
    ct0="5db60afa1919235fe30bce9988bba078850738d7a9abb564dfa592c8f6021e113d03eee580eba7b102d009b89d598478ba374421707cd9266140790a42005b05c2e6ac863bcbebcef3ffe767589705c7",
    auth_token="b40112fc07430f6708c1e0463b8a4c9bad51554e"
)