using UnityEngine;

public class NPCController : MonoBehaviour
{
    public void ApplyDecision(string json, AudioClip voiceClip)
    {
        NPCResponse response = JsonUtility.FromJson<NPCResponse>(json);

        // Play NPC voice
        if (voiceClip != null)
        {
            AudioSource audioSource = GetComponent<AudioSource>();
            audioSource.clip = voiceClip;
            audioSource.Play();
        }

        // Execute NPC action
        switch (response.action)
        {
            case "point":      PointAtTarget(response.target); break;
            case "give_quest": TriggerQuest(response.target);  break;
            case "open_shop":  OpenShop(response.target);      break;
        }
    }

    private void PointAtTarget(string targetId)
    {
        // Requires a GameObject named after the targetId to exist in the scene
        // Create empty GameObjects: "tavern", "blacksmith", "market", etc.
        GameObject target = GameObject.Find(targetId);
        if (target != null)
        {
            transform.LookAt(target.transform);
            // Animator.SetTrigger("Point");
        }
    }

    private void TriggerQuest(string questId)
    {
        // Stub — connect your own quest system here
        // QuestManager.Instance.StartQuest(questId);
        Debug.Log("Quest started: " + questId);
    }

    private void OpenShop(string shopId)
    {
        // Stub — connect your own shop UI here
        // ShopUI.Instance.Open(shopId);
        Debug.Log("Shop opened: " + shopId);
    }
}
