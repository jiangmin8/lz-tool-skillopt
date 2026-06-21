#!/usr/bin/env python3
"""Prepare SearchQA dataset for SkillOpt."""
import json
import os

from datasets import load_dataset


def main():
    # Load raw dataset from HuggingFace
    print("Loading SearchQA dataset from HuggingFace...")
    ds = load_dataset("lucadiliello/searchqa")
    
    # Build id -> item mapping
    print("Building ID mapping...")
    id_to_item = {}
    for split in ['train', 'validation']:
        for item in ds[split]:
            item_id = item.get('key', item.get('id'))
            if item_id:
                id_to_item[item_id] = item
    
    print(f"Total items: {len(id_to_item)}")
    
    # Load manifest IDs
    manifest_dir = "data/searchqa_id_split"
    splits = ['train', 'val', 'test']
    
    # Create output directory
    output_dir = "data/searchqa_split"
    os.makedirs(output_dir, exist_ok=True)
    
    for split_name in splits:
        manifest_path = os.path.join(manifest_dir, split_name, "items.json")
        output_split_dir = os.path.join(output_dir, split_name)
        os.makedirs(output_split_dir, exist_ok=True)
        
        with open(manifest_path) as f:
            manifest_items = json.load(f)
        
        materialized_items = []
        for manifest_item in manifest_items:
            item_id = manifest_item.get('id')
            if item_id in id_to_item:
                raw_item = id_to_item[item_id]
                # Extract required fields
                materialized = {
                    'id': item_id,
                    'question': raw_item.get('question', ''),
                    'context': raw_item.get('context', ''),
                    'answers': raw_item.get('answers', []),
                }
                materialized_items.append(materialized)
        
        output_path = os.path.join(output_split_dir, "items.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(materialized_items, f, ensure_ascii=False, indent=2)
        
        print(f"{split_name}: {len(materialized_items)} items saved to {output_path}")
    
    print("\nSearchQA dataset prepared successfully!")


if __name__ == "__main__":
    main()