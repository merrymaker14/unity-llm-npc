using UnityEngine;

[System.Serializable]
public class Place
{
    public string id;
    public string name;
}

[System.Serializable]
public class WorldContext
{
    public string time_of_day;
    public string village;
    public Place[] places;
}

public class WorldContextBuilder : MonoBehaviour
{
    public string GetContextJson()
    {
        var ctx = new WorldContext
        {
            time_of_day = GetTimeOfDay(),
            village = "Ashen Pass",
            places = new Place[]
            {
                new Place { id = "tavern",     name = "The Drunk Dragon Tavern"      },
                new Place { id = "blacksmith", name = "The Red Forge Blacksmith"     },
                new Place { id = "market",     name = "The Silver Crossroads Market" },
                new Place { id = "tower",      name = "The Silent One Tower"         },
                new Place { id = "crypt",      name = "The Founders Crypt"           },
                new Place { id = "alchemist",  name = "The Crooked Mirror Alchemist" }
            }
        };
        return JsonUtility.ToJson(ctx);
    }

    private string GetTimeOfDay()
    {
        int hour = System.DateTime.Now.Hour;
        if (hour < 6)  return "night";
        if (hour < 12) return "morning";
        if (hour < 18) return "afternoon";
        return "evening";
    }
}
