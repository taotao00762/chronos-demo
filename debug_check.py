"""Quick debug script to check database data."""
import asyncio
import sys
sys.path.insert(0, 'E:/baoke/chronos')

async def main():
    from db.dao import ReceiptDAO, MasteryDAO, EvidenceDAO
    
    print("=== Database Check ===")
    
    receipts = await ReceiptDAO.list_recent(20)
    print(f"\nReceipts: {len(receipts)}")
    for r in receipts[:5]:
        topics = r.get("topics_json", [])
        print(f"  - {topics[:50] if isinstance(topics, str) else topics}")
    
    mastery = await MasteryDAO.list_all()
    print(f"\nMastery: {len(mastery)}")
    for m in mastery[:5]:
        print(f"  - {m.get('concept', '')}: {m.get('level', 0)}")
    
    evidence = await EvidenceDAO.list_recent(20)
    print(f"\nEvidence: {len(evidence)}")
    for e in evidence[:5]:
        print(f"  - [{e.get('type')}] {e.get('summary', '')[:50]}")

if __name__ == "__main__":
    asyncio.run(main())
