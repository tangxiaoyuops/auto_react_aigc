#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Joke Generator Script
Generates jokes based on topic, style, and count parameters.
"""

import argparse
import json
import random
import sys

# 简易笑话模板库 (实际生产中可替换为调用大模型或更复杂的数据库)
JOKE_TEMPLATES = {
    "tech": [
        "为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 == Dec 25。",
        "{topic}专家最讨厌什么？讨厌别人问他们‘这个功能很简单，能不能加个按钮’。",
        "有个{topic}去相亲，对方问：‘你有房吗？’他答：‘我有云存储。'"
    ],
    "cold": [
        "有一根火柴，觉得头很痒，就抓了抓，然后……它着火了。",
        "为什么企鹅只有肚子是白的？因为手短洗不到后背。",
        "透明人最讨厌什么？最讨厌被别人看穿。"
    ],
    "pun": [
        "什么动物最容易被贴在墙上？海豹（海报）。",
        "哪种水果最老实？芭蕉（交）。",
        "为什么大雁秋天要飞到南方去？因为走过去太远了。"
    ],
    "scenario": [
        "老婆：‘如果我和你妈同时掉水里，你先救谁？’老公：‘我妈会游泳，她还能救你。'",
        "老板：‘公司就是你的家。’我：‘那我能在家里穿睡衣躺平吗？’老板：‘滚出去。'"
    ]
}

def generate_joke(topic, style):
    """根据风格和主题生成单个笑话"""
    # 确定风格
    if style == "random" or style not in JOKE_TEMPLATES:
        style = random.choice(list(JOKE_TEMPLATES.keys()))
    
    templates = JOKE_TEMPLATES[style]
    template = random.choice(templates)
    
    # 简单的主题替换逻辑
    if "{topic}" in template and topic:
        return template.format(topic=topic)
    elif topic and "随机" not in template:
        # 尝试将主题强行融入（简单策略：追加或替换通用词）
        return f"关于{topic}的笑话：{template}"
    
    return template

def main():
    parser = argparse.ArgumentParser(description="Generate jokes based on parameters.")
    parser.add_argument("--topic", type=str, default="", help="Topic or keyword for the joke.")
    parser.add_argument("--style", type=str, default="random", 
                        choices=["cold", "pun", "scenario", "tech", "random"],
                        help="Style of the joke.")
    parser.add_argument("--count", type=int, default=1, help="Number of jokes to generate.")
    
    args = parser.parse_args()
    
    results = []
    for _ in range(args.count):
        joke_text = generate_joke(args.topic, args.style)
        results.append({
            "content": joke_text,
            "style": args.style,
            "topic": args.topic if args.topic else "general"
        })
    
    output = {
        "status": "success",
        "count": len(results),
        "data": results
    }
    
    # 必须打印 JSON 到 stdout 供 Agent 解析
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
