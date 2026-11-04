Shader "Shakedown/Spike/Lit atmosphere rim"
{
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "Queue"="Transparent+10" }
        Pass
        {
            Blend One One
            ZWrite Off
            Cull Front
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            struct Input { float4 position:POSITION; float3 normal:NORMAL; };
            struct Varying { float4 position:SV_POSITION; float3 world:TEXCOORD0; half3 normal:TEXCOORD1; };
            Varying Vert(Input v) { Varying o; o.world=TransformObjectToWorld(v.position.xyz); o.position=TransformWorldToHClip(o.world); o.normal=TransformObjectToWorldNormal(v.normal); return o; }
            half4 Frag(Varying i):SV_Target
            {
                half3 n=normalize(i.normal); half3 v=normalize(_WorldSpaceCameraPos-i.world);
                half rim=pow(1-abs(dot(n,v)),5);
                half lit=saturate(dot(n,GetMainLight().direction)*2);
                return half4(half3(.12,.32,.52)*rim*lit*.7,1);
            }
            ENDHLSL
        }
    }
}
