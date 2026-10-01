This is a project to create a web app for anybody to learn history and geography using animated maps. This can be split into two major parts:
- A lesson/test renderer (the web app to display animated maps).
- A lesson/test research and creator (an agent skill to research specific geography and/or history topics given by the user, and turn the research results into a machine-readable structured format, which can be replayed by the renderer; using the same research results, create some tests for the learner to verify and strengthen their knowledge).

Example use cases:
- Learning country names:
  - Learning mode: a map of each continent for the learner to learn the names and locations of the countries: show the map with only national borders drawn initially, then click on a country to reveal its name and a tooltip with additional info (e.g. population, demographics, demonym, ethnicities, date or year of foundation, date or year of collapse in the case of historical maps);
  - Test mode: same map, still with only national borders drawn. There are two forms of test:
    - The learner is given a country name and is tasked with correctly locating the country on the map. The learner must locate the countries one by one, maybe only a fixed number or fixed fraction of countries on the continent, or all of them.
    - A country is highlighted on the map and the learner is tasked with given the correct name of the country, either with multiple choice or free text input.
- Learning how historical events happened across the world.
  - Some examples:
    - Important warfare campaigns, how the participating forces moved, how the frontlines and positions changed over time. With animated arrows, different colours to distinguish the territories controlled by different forces, standards/banners to identify the forces. In learning mode, explanatory text is shown as the learner steps through the timeline of the campaign.
    - Important voyages - e.g. the Magellan expedition, the Zheng He expeditions, Xuanzang's pilgrimage.
      - For sea voyages, make sure the crew does not accidentally cross over land during animation, unless history really says they landed and went through land.
      - For land voyages, make sure the traveller does not accidentally cross over seas and oceans or other historically insurmountable geographical feature in the animation. E.g. There's no way Xuanzang could directly scale the Himalayas. He took a long detour.
  - In test mode, the map is rendered as the situation of the campaign or voyage at a certain point in time, and then the app asks the learner to select where an actor (a particular armed unit or a crew) went next according to history (e.g. show three arrows pointing to different destinations, and the learner is supposed to click on the correct one).

By the way, the app and learning material needs to be multilingual, let's say we support British English, Canadian French, Simplified Chinese (Mainland China), and Traditional Chinese (Hong Kong) for now.
