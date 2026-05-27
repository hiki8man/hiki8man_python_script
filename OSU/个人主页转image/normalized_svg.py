from bs4 import BeautifulSoup, NavigableString
import re
def css_to_svg_transform(css_value: str) -> str:
    func_pattern = re.compile(
        r'(translateX|translateY|translate|scale|rotate|skewX|skewY|matrix)\s*\(([^)]+)\)'
    )

    parts = []
    for func_match in func_pattern.finditer(css_value):
        func_name = func_match.group(1)
        args = func_match.group(2).strip()
        args = re.sub(r'px\b', '', args)
        args = re.sub(r'\s*,\s*', ',', args)
        args = re.sub(r'\s+', ' ', args)

        if func_name == 'translateX':
            parts.append(f'translate({args}, 0)')
        elif func_name == 'translateY':
            parts.append(f'translate(0, {args})')
        else:
            parts.append(f'{func_name}({args})')

    return ' '.join(parts)


def extract_css_transforms(soup: BeautifulSoup) -> dict:
    css_transforms = {}

    for style_tag in soup.find_all('style'):
        if not style_tag.string:
            continue

        css_text = style_tag.string
        rule_pattern = re.compile(
            r'\.([\w-]+)\s*\{([^}]*)\}', re.DOTALL
        )

        for match in rule_pattern.finditer(css_text):
            class_name = match.group(1)
            body = match.group(2)
            transform_match = re.search(r'transform\s*:\s*([^;}]+)', body)
            if transform_match:
                css_val = transform_match.group(1).strip()
                css_transforms[class_name] = css_to_svg_transform(css_val)

    return css_transforms

def remove_css_transform_rules(soup: BeautifulSoup):
    for style_tag in soup.find_all('style'):
        if not style_tag.string:
            continue

        css_text = style_tag.string
        result = re.sub(
            r'\s*transform\s*:\s*[^;]+;?',
            '',
            css_text
        )
        # 清理空的花括号（规则中所有属性都被删了的情况）
        result = re.sub(r'\.([\w-]+)\s*\{\s*\}', '', result)
        # 清理多余空行
        result = re.sub(r'\n{3,}', '\n\n', result)
        style_tag.string.replace_with(result)

    # 删除空的 <style></style>
    for style_tag in soup.find_all('style'):
        text = style_tag.string.strip() if style_tag.string else ''
        if not text:
            style_tag.decompose()

def apply_transform_to_elements(soup: BeautifulSoup, css_transforms: dict):
    for class_name, svg_transform in css_transforms.items():
        for tag in soup.select(f'.{class_name}'):
            existing = tag.get('transform', '')
            if existing:
                tag['transform'] = f'{existing} {svg_transform}'
            else:
                tag['transform'] = svg_transform

def flatten_tspans(soup: BeautifulSoup):
    """
    展平嵌套的 <tspan>：
    <tspan><tspan>xx</tspan> with <tspan>yy</tspan></tspan>
    →
    <tspan>xx with yy</tspan>

    保留最外层 <tspan> 的属性（x, y, dx, dy, font-weight, fill 等）
    """
    changed = True
    while changed:
        changed = False
        for tspan in soup.find_all('tspan'):
            # 检查是否有子 tspan
            inner_tspans = tspan.find_all('tspan', recursive=False)
            if not inner_tspans:
                continue

            # 收集子 tspan 中的所有文本内容和属性
            # 策略：删除所有内层 tspan 标签，只保留文本
            inner_text_parts = []
            for child in list(tspan.children):
                if isinstance(child, NavigableString):
                    text = str(child)
                    if text.strip():
                        inner_text_parts.append(text)
                elif child.name == 'tspan':
                    # 取子 tspan 的文本内容
                    inner_text_parts.append(child.get_text())
                else:
                    inner_text_parts.append(child.get_text())

            # 用纯文本替换 tspan 的内容
            combined_text = ''.join(inner_text_parts)
            tspan.clear()
            tspan.append(combined_text)
            changed = True


def normalized_svg(svg_content: str) -> str:
    soup = BeautifulSoup(svg_content, 'lxml-xml')
    # plutobook不支持内嵌tspan，需要删除嵌套，这样代价是缺失样式
    flatten_tspans(soup)

    css_transforms = extract_css_transforms(soup)

    if css_transforms:
        apply_transform_to_elements(soup, css_transforms)
        remove_css_transform_rules(soup)

    return str(soup)